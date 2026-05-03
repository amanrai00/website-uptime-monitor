"""Website uptime monitor Lambda handler."""

from __future__ import annotations

import json
import logging
import os
import socket
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def get_config() -> dict[str, Any]:
    return {
        "target_url": os.environ["TARGET_URL"],
        "timeout_seconds": int(os.environ.get("TIMEOUT_SECONDS", "10")),
        "response_threshold_ms": int(os.environ.get("RESPONSE_THRESHOLD_MS", "3000")),
        "sns_topic_arn": os.environ.get("SNS_TOPIC_ARN"),
        "dynamodb_table": os.environ.get("DYNAMODB_TABLE", "website_checks"),
        "site_id": os.environ.get("SITE_ID", "default-site"),
        "s3_bucket": os.environ.get("S3_BUCKET"),
        "s3_status_key": os.environ.get("S3_STATUS_KEY", "status.json"),
        "expected_text": os.environ.get("EXPECTED_TEXT"),
        "forbidden_text": os.environ.get("FORBIDDEN_TEXT"),
    }


def run_http_check(url: str, timeout_seconds: int) -> dict[str, Any]:
    start = time.time()
    status_code = None
    failure_reason = None
    response_body = ""

    try:
        request = urllib.request.Request(url, method="GET")
        # urllib follows redirects by default; evaluate final resolved status code.
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            status_code = response.getcode()
            response_body = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        status_code = exc.code
        failure_reason = f"HTTP {exc.code}: {exc.reason}"
    except socket.timeout:
        failure_reason = "Request timed out"
    except urllib.error.URLError as exc:
        failure_reason = f"URL error: {exc.reason}"
    except Exception as exc:  # noqa: BLE001 - Lambda must record unknown failure types.
        failure_reason = f"{type(exc).__name__}: {exc}"

    response_time_ms = int(round((time.time() - start) * 1000))

    return {
        "status_code": status_code,
        "response_time_ms": response_time_ms,
        "failure_reason": failure_reason,
        "response_body": response_body,
    }


def build_result(
    *,
    site_id: str,
    check_time: str,
    url: str,
    status_code: int | None,
    response_time_ms: int,
    response_threshold_ms: int,
    failure_reason: str | None,
    response_body: str,
    expected_text: str | None,
    forbidden_text: str | None,
) -> dict[str, Any]:
    is_success = failure_reason is None
    content_check_passed = True

    if is_success and (status_code is None or not 200 <= status_code <= 299):
        is_success = False
        failure_reason = f"HTTP status outside 200-299: {status_code or 'N/A'}"

    if is_success and response_time_ms > response_threshold_ms:
        is_success = False
        failure_reason = (
            f"Slow response: {response_time_ms}ms exceeds "
            f"{response_threshold_ms}ms threshold"
        )

    if is_success and expected_text and expected_text not in response_body:
        is_success = False
        content_check_passed = False
        failure_reason = f"Expected text not found: '{expected_text}'"

    if is_success and forbidden_text and forbidden_text in response_body:
        is_success = False
        content_check_passed = False
        failure_reason = f"Forbidden text found: '{forbidden_text}'"

    return {
        "site_id": site_id,
        "check_time": check_time,
        "url": url,
        "status_code": status_code,
        "response_time_ms": response_time_ms,
        "is_success": is_success,
        "failure_reason": failure_reason,
        "content_check_passed": content_check_passed,
    }


def without_null_values(item: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in item.items() if value is not None}


def build_status_payload(
    result: dict[str, Any], recent_failures: list[dict[str, Any]]
) -> dict[str, Any]:
    return {
        "site_id": result["site_id"],
        "url": result["url"],
        "last_checked": result["check_time"],
        "status": "UP" if result["is_success"] else "DOWN",
        "status_code": result["status_code"],
        "response_time_ms": result["response_time_ms"],
        "is_success": result["is_success"],
        "failure_reason": result["failure_reason"],
        "content_check_passed": result["content_check_passed"],
        "recent_failures": recent_failures,
    }


def write_result_to_dynamodb(table_name: str, result: dict[str, Any]) -> None:
    import boto3

    table = boto3.resource("dynamodb").Table(table_name)
    table.put_item(Item=without_null_values(result))


def _as_int(value: Any) -> int | None:
    return int(value) if value is not None else None


def build_failure_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "check_time": item.get("check_time"),
        "status_code": _as_int(item.get("status_code")),
        "response_time_ms": _as_int(item.get("response_time_ms")),
        "failure_reason": item.get("failure_reason"),
    }


def get_recent_failures(
    table_name: str,
    site_id: str,
    current_result: dict[str, Any],
    query_limit: int = 50,
    failure_limit: int = 5,
) -> list[dict[str, Any]]:
    import boto3
    from boto3.dynamodb.conditions import Key

    print(f"recent failures query started for site_id={site_id}")
    table = boto3.resource("dynamodb").Table(table_name)
    try:
        response = table.query(
            KeyConditionExpression=Key("site_id").eq(site_id),
            ScanIndexForward=False,
            Limit=query_limit,
        )
    except Exception as exc:
        print(f"recent failures query error: {type(exc).__name__}: {exc}")
        raise

    items = response.get("Items", [])
    print(f"recent failures DynamoDB records returned: {len(items)}")

    failures = [build_failure_item(item) for item in items if item.get("is_success") is False]
    print(f"recent failures failed records found from query: {len(failures)}")

    current_added = False
    if current_result["is_success"] is False:
        current_failure = build_failure_item(current_result)
        if not any(
            failure.get("check_time") == current_failure["check_time"]
            for failure in failures
        ):
            failures.append(current_failure)
            current_added = True

    print(f"recent failures current failed check added manually: {current_added}")

    recent_failures = []
    seen_check_times = set()
    for failure in sorted(
        failures, key=lambda item: item.get("check_time") or "", reverse=True
    ):
        check_time = failure.get("check_time")
        if check_time in seen_check_times:
            continue

        seen_check_times.add(check_time)
        recent_failures.append(failure)

        if len(recent_failures) == failure_limit:
            break

    print(f"recent failures final count written to status.json: {len(recent_failures)}")
    return recent_failures


def write_status_to_s3(bucket: str, key: str, payload: dict[str, Any]) -> None:
    import boto3

    boto3.client("s3").put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(payload),
        ContentType="application/json",
        CacheControl="no-cache",
    )


def publish_failure_alert(topic_arn: str, result: dict[str, Any]) -> None:
    import boto3

    status_code = result["status_code"] if result["status_code"] is not None else "N/A"
    message = (
        f"URL: {result['url']}\n"
        f"Failure reason: {result['failure_reason']}\n"
        f"Status code: {status_code}\n"
        f"Response time: {result['response_time_ms']}ms\n"
        f"Timestamp: {result['check_time']}"
    )

    # MVP alerts on every failure; consecutive-failure threshold is a Version 2 improvement.
    boto3.client("sns").publish(
        TopicArn=topic_arn,
        Subject=f"{result['site_id']} DOWN",
        Message=message,
    )


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    config = get_config()
    check_time = utc_now_iso()
    check = run_http_check(config["target_url"], config["timeout_seconds"])
    result = build_result(
        site_id=config["site_id"],
        check_time=check_time,
        url=config["target_url"],
        status_code=check["status_code"],
        response_time_ms=check["response_time_ms"],
        response_threshold_ms=config["response_threshold_ms"],
        failure_reason=check["failure_reason"],
        response_body=check["response_body"],
        expected_text=config["expected_text"],
        forbidden_text=config["forbidden_text"],
    )

    write_result_to_dynamodb(config["dynamodb_table"], result)

    recent_failures = get_recent_failures(
        config["dynamodb_table"], config["site_id"], result
    )
    status_payload = build_status_payload(result, recent_failures)
    if config["s3_bucket"]:
        write_status_to_s3(config["s3_bucket"], config["s3_status_key"], status_payload)
    else:
        logger.warning("S3_BUCKET not configured, skipping dashboard write")

    if not result["is_success"] and config["sns_topic_arn"]:
        publish_failure_alert(config["sns_topic_arn"], result)

    logger.info("Uptime check result: %s", json.dumps(result))
    return result

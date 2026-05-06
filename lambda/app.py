"""Website uptime monitor Lambda handler."""

from __future__ import annotations

import json
import logging
import os
import socket
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

SUPPORTED_REDIRECT_POLICIES = {"follow", "fail_on_redirect"}
REDIRECT_STATUS_CODES = {301, 302, 303, 307, 308}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def get_config() -> dict[str, Any]:
    sites = parse_sites_config(os.environ.get("SITES_CONFIG"))
    if not sites:
        sites = [get_single_site_config()]

    return {
        "sns_topic_arn": os.environ.get("SNS_TOPIC_ARN"),
        "alert_failure_threshold": int(os.environ.get("ALERT_FAILURE_THRESHOLD", "2")),
        "retention_days": parse_positive_int(os.environ.get("RETENTION_DAYS"), 30),
        "dynamodb_table": os.environ.get("DYNAMODB_TABLE", "website_checks"),
        "s3_bucket": os.environ.get("S3_BUCKET"),
        "s3_status_key": os.environ.get("S3_STATUS_KEY", "status.json"),
        "sites": sites,
    }


def get_single_site_config() -> dict[str, Any]:
    return {
        "site_id": os.environ.get("SITE_ID", "default-site"),
        "target_url": os.environ["TARGET_URL"],
        "timeout_seconds": int(os.environ.get("TIMEOUT_SECONDS", "10")),
        "response_threshold_ms": int(os.environ.get("RESPONSE_THRESHOLD_MS", "3000")),
        "expected_text": os.environ.get("EXPECTED_TEXT"),
        "forbidden_text": os.environ.get("FORBIDDEN_TEXT"),
        "redirect_policy": normalize_redirect_policy(
            os.environ.get("REDIRECT_POLICY", "follow")
        ),
    }


def parse_sites_config(raw_config: str | None) -> list[dict[str, Any]]:
    if not raw_config:
        return []

    sites_config = json.loads(raw_config)
    if not sites_config:
        return []
    if not isinstance(sites_config, list):
        raise ValueError("SITES_CONFIG must be a JSON array")

    return [
        normalize_site_config(site_config, index)
        for index, site_config in enumerate(sites_config, start=1)
    ]


def normalize_site_config(site_config: Any, index: int) -> dict[str, Any]:
    if not isinstance(site_config, dict):
        raise ValueError(f"SITES_CONFIG item {index} must be an object")

    site_id = site_config.get("site_id")
    target_url = site_config.get("target_url")
    if not site_id:
        raise ValueError(f"SITES_CONFIG item {index} missing site_id")
    if not target_url:
        raise ValueError(f"SITES_CONFIG item {index} missing target_url")

    return {
        "site_id": str(site_id),
        "target_url": str(target_url),
        "timeout_seconds": int(site_config.get("timeout_seconds", 10)),
        "response_threshold_ms": int(site_config.get("response_threshold_ms", 3000)),
        "expected_text": site_config.get("expected_text"),
        "forbidden_text": site_config.get("forbidden_text"),
        "redirect_policy": normalize_redirect_policy(
            site_config.get("redirect_policy", "follow")
        ),
    }


def normalize_redirect_policy(redirect_policy: Any) -> str:
    normalized_policy = str(redirect_policy or "follow")
    if normalized_policy not in SUPPORTED_REDIRECT_POLICIES:
        raise ValueError(
            "redirect_policy must be one of: follow, fail_on_redirect"
        )
    return normalized_policy


def parse_positive_int(value: Any, default: int) -> int:
    try:
        parsed_value = int(value)
    except (TypeError, ValueError):
        return default
    return parsed_value if parsed_value > 0 else default


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


def run_http_check(
    url: str, timeout_seconds: int, redirect_policy: str = "follow"
) -> dict[str, Any]:
    start = time.time()
    status_code = None
    failure_reason = None
    response_body = ""
    redirect_detected = False

    try:
        request = urllib.request.Request(url, method="GET")
        if redirect_policy == "fail_on_redirect":
            opener = urllib.request.build_opener(NoRedirectHandler)
            open_url = opener.open
        else:
            # urllib follows redirects by default; evaluate final resolved status code.
            open_url = urllib.request.urlopen

        with open_url(request, timeout=timeout_seconds) as response:
            status_code = response.getcode()
            redirect_detected = response.geturl() != request.full_url
            response_body = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        status_code = exc.code
        redirect_detected = exc.code in REDIRECT_STATUS_CODES
        if redirect_policy == "fail_on_redirect" and redirect_detected:
            failure_reason = f"Redirect not allowed: HTTP {exc.code}"
        else:
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
        "redirect_detected": redirect_detected,
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
    response_body: str = "",
    expected_text: str | None = None,
    forbidden_text: str | None = None,
    redirect_policy: str = "follow",
    redirect_detected: bool = False,
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
        "redirect_policy": redirect_policy,
        "redirect_detected": redirect_detected,
    }


def without_null_values(item: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in item.items() if value is not None}


def to_dynamodb_value(value: Any) -> Any:
    if isinstance(value, float):
        return Decimal(str(value))
    return value


def build_dynamodb_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        key: to_dynamodb_value(value)
        for key, value in without_null_values(item).items()
    }


def build_status_payload(
    result: dict[str, Any], recent_failures: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    if recent_failures is None:
        recent_failures = []

    return {
        "site_id": result["site_id"],
        "url": result["url"],
        "last_checked": result["check_time"],
        "status": "UP" if result["is_success"] else "DOWN",
        "status_code": result["status_code"],
        "response_time_ms": result["response_time_ms"],
        "uptime_percentage": result.get("uptime_percentage"),
        "uptime_window_checks": result.get("uptime_window_checks"),
        "average_response_time_ms": result.get("average_response_time_ms"),
        "response_time_window_checks": result.get("response_time_window_checks"),
        "incident_count_24h": result.get("incident_count_24h"),
        "incident_count_7d": result.get("incident_count_7d"),
        "consecutive_failure_count": result["consecutive_failure_count"],
        "alert_sent": result["alert_sent"],
        "alert_failure_threshold": result["alert_failure_threshold"],
        "ttl_expires_at": result["ttl_expires_at"],
        "redirect_policy": result["redirect_policy"],
        "redirect_detected": result["redirect_detected"],
        "is_success": result["is_success"],
        "failure_reason": result["failure_reason"],
        "content_check_passed": result["content_check_passed"],
        "recent_failures": recent_failures,
    }


def build_multi_status_payload(
    site_payloads: list[dict[str, Any]]
) -> dict[str, Any]:
    payload = site_payloads[0].copy()
    payload["sites"] = site_payloads
    payload["site_count"] = len(site_payloads)
    payload["status"] = "UP" if all(site["is_success"] for site in site_payloads) else "DOWN"
    payload["is_success"] = all(site["is_success"] for site in site_payloads)
    return payload


def write_result_to_dynamodb(table_name: str, result: dict[str, Any]) -> None:
    import boto3

    table = boto3.resource("dynamodb").Table(table_name)
    table.put_item(Item=build_dynamodb_item(result))


def _as_int(value: Any) -> int | None:
    return int(value) if value is not None else None


def build_failure_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "check_time": item.get("check_time"),
        "status_code": _as_int(item.get("status_code")),
        "response_time_ms": _as_int(item.get("response_time_ms")),
        "failure_reason": item.get("failure_reason"),
    }


def calculate_uptime_metrics(
    current_result: dict[str, Any],
    recent_items: list[dict[str, Any]],
    window_limit: int = 50,
) -> dict[str, Any]:
    site_id = current_result["site_id"]
    records = [current_result]
    seen_check_times = {current_result.get("check_time")}

    for item in recent_items:
        if item.get("site_id") != site_id:
            continue
        check_time = item.get("check_time")
        if check_time in seen_check_times:
            continue

        seen_check_times.add(check_time)
        records.append(item)

        if len(records) == window_limit:
            break

    total_checks = len(records)
    successful_checks = sum(1 for item in records if item.get("is_success") is True)
    uptime_percentage = round((successful_checks / total_checks) * 100, 2)

    return {
        "uptime_percentage": uptime_percentage,
        "uptime_window_checks": total_checks,
    }


def calculate_response_time_metrics(
    current_result: dict[str, Any],
    recent_items: list[dict[str, Any]],
    window_limit: int = 50,
) -> dict[str, Any]:
    site_id = current_result["site_id"]
    response_times = []
    seen_check_times = {current_result.get("check_time")}

    current_response_time = current_result.get("response_time_ms")
    if current_response_time is not None:
        response_times.append(_as_int(current_response_time))

    for item in recent_items:
        if item.get("site_id") != site_id:
            continue
        check_time = item.get("check_time")
        if check_time in seen_check_times:
            continue

        seen_check_times.add(check_time)
        response_time = item.get("response_time_ms")
        if response_time is not None:
            response_times.append(_as_int(response_time))

        if len(response_times) == window_limit:
            break

    if not response_times:
        return {
            "average_response_time_ms": None,
            "response_time_window_checks": 0,
        }

    average_response_time_ms = int(round(sum(response_times) / len(response_times)))

    return {
        "average_response_time_ms": average_response_time_ms,
        "response_time_window_checks": len(response_times),
    }


def parse_check_time(check_time: str | None) -> datetime | None:
    if not check_time:
        return None
    try:
        parsed_check_time = datetime.fromisoformat(check_time.replace("Z", "+00:00"))
    except ValueError:
        return None

    if parsed_check_time.tzinfo is None:
        return parsed_check_time.replace(tzinfo=timezone.utc)
    return parsed_check_time


def calculate_incident_metrics(
    current_result: dict[str, Any],
    recent_items: list[dict[str, Any]],
) -> dict[str, int]:
    site_id = current_result["site_id"]
    reference_time = parse_check_time(current_result.get("check_time"))
    if reference_time is None:
        reference_time = datetime.now(timezone.utc)

    cutoff_24h = reference_time - timedelta(hours=24)
    cutoff_7d = reference_time - timedelta(days=7)
    failed_check_times = []
    seen_check_times = set()

    for item in [current_result, *recent_items]:
        if item.get("site_id") != site_id:
            continue
        if item.get("is_success") is not False:
            continue

        check_time = item.get("check_time")
        if check_time in seen_check_times:
            continue

        parsed_check_time = parse_check_time(check_time)
        if parsed_check_time is None:
            continue

        seen_check_times.add(check_time)
        failed_check_times.append(parsed_check_time)

    return {
        "incident_count_24h": sum(
            1 for check_time in failed_check_times if check_time >= cutoff_24h
        ),
        "incident_count_7d": sum(
            1 for check_time in failed_check_times if check_time >= cutoff_7d
        ),
    }


def calculate_consecutive_failure_count(
    current_result: dict[str, Any],
    recent_items: list[dict[str, Any]],
) -> int:
    if current_result["is_success"]:
        return 0

    site_id = current_result["site_id"]
    consecutive_failures = 1
    seen_check_times = {current_result.get("check_time")}

    for item in recent_items:
        if item.get("site_id") != site_id:
            continue

        check_time = item.get("check_time")
        if check_time in seen_check_times:
            continue
        seen_check_times.add(check_time)

        if item.get("is_success") is True:
            break
        if item.get("is_success") is False:
            consecutive_failures += 1

    return consecutive_failures


def calculate_ttl_expires_at(check_time: str | None, retention_days: int) -> int:
    parsed_check_time = parse_check_time(check_time)
    if parsed_check_time is None:
        parsed_check_time = datetime.now(timezone.utc)

    expires_at = parsed_check_time + timedelta(days=retention_days)
    return int(expires_at.timestamp())


def get_recent_results(
    table_name: str,
    site_id: str,
    query_limit: int = 50,
) -> list[dict[str, Any]]:
    import boto3
    from boto3.dynamodb.conditions import Key

    table = boto3.resource("dynamodb").Table(table_name)
    response = table.query(
        KeyConditionExpression=Key("site_id").eq(site_id),
        ScanIndexForward=False,
        Limit=query_limit,
    )
    return response.get("Items", [])


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


def check_site(config: dict[str, Any], site_config: dict[str, Any], check_time: str) -> dict[str, Any]:
    check = run_http_check(
        site_config["target_url"],
        site_config["timeout_seconds"],
        site_config["redirect_policy"],
    )
    result = build_result(
        site_id=site_config["site_id"],
        check_time=check_time,
        url=site_config["target_url"],
        status_code=check["status_code"],
        response_time_ms=check["response_time_ms"],
        response_threshold_ms=site_config["response_threshold_ms"],
        failure_reason=check["failure_reason"],
        response_body=check["response_body"],
        expected_text=site_config["expected_text"],
        forbidden_text=site_config["forbidden_text"],
        redirect_policy=site_config["redirect_policy"],
        redirect_detected=check["redirect_detected"],
    )

    recent_results = get_recent_results(config["dynamodb_table"], site_config["site_id"])
    result.update(calculate_uptime_metrics(result, recent_results))
    result.update(calculate_response_time_metrics(result, recent_results))
    result.update(calculate_incident_metrics(result, recent_results))
    result["consecutive_failure_count"] = calculate_consecutive_failure_count(
        result, recent_results
    )
    result["alert_failure_threshold"] = config["alert_failure_threshold"]
    result["ttl_expires_at"] = calculate_ttl_expires_at(
        result["check_time"], config["retention_days"]
    )
    result["alert_sent"] = (
        not result["is_success"]
        and result["consecutive_failure_count"] >= config["alert_failure_threshold"]
        and bool(config["sns_topic_arn"])
    )
    recent_failures = get_recent_failures(
        config["dynamodb_table"], site_config["site_id"], result
    )
    write_result_to_dynamodb(config["dynamodb_table"], result)

    if result["alert_sent"]:
        publish_failure_alert(config["sns_topic_arn"], result)

    logger.info("Uptime check result: %s", json.dumps(result))
    return {
        "result": result,
        "status_payload": build_status_payload(result, recent_failures),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    config = get_config()
    check_time = utc_now_iso()
    checked_sites = [
        check_site(config, site_config, check_time)
        for site_config in config["sites"]
    ]

    site_payloads = [site["status_payload"] for site in checked_sites]
    status_payload = (
        site_payloads[0]
        if len(site_payloads) == 1
        else build_multi_status_payload(site_payloads)
    )
    if config["s3_bucket"]:
        write_status_to_s3(config["s3_bucket"], config["s3_status_key"], status_payload)
    else:
        logger.warning("S3_BUCKET not configured, skipping dashboard write")

    results = [site["result"] for site in checked_sites]
    return results[0] if len(results) == 1 else {"sites": results}

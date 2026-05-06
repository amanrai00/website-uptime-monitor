from importlib import import_module


app = import_module("lambda.app")
build_result = app.build_result
build_status_payload = app.build_status_payload
calculate_incident_metrics = app.calculate_incident_metrics
calculate_consecutive_failure_count = app.calculate_consecutive_failure_count
calculate_ttl_expires_at = app.calculate_ttl_expires_at
calculate_response_time_metrics = app.calculate_response_time_metrics
calculate_uptime_metrics = app.calculate_uptime_metrics
check_site = app.check_site
get_config = app.get_config
parse_sites_config = app.parse_sites_config
without_null_values = app.without_null_values


def test_parse_sites_config_returns_multi_site_configs():
    sites = parse_sites_config(
        """
        [
          {
            "site_id": "my-portfolio",
            "target_url": "https://example.com",
            "timeout_seconds": 10,
            "response_threshold_ms": 3000,
            "expected_text": "Example Domain",
            "forbidden_text": "",
            "redirect_policy": "fail_on_redirect"
          },
          {
            "site_id": "docs",
            "target_url": "https://docs.example.com"
          }
        ]
        """
    )

    assert sites == [
        {
            "site_id": "my-portfolio",
            "target_url": "https://example.com",
            "timeout_seconds": 10,
            "response_threshold_ms": 3000,
            "expected_text": "Example Domain",
            "forbidden_text": "",
            "redirect_policy": "fail_on_redirect",
        },
        {
            "site_id": "docs",
            "target_url": "https://docs.example.com",
            "timeout_seconds": 10,
            "response_threshold_ms": 3000,
            "expected_text": None,
            "forbidden_text": None,
            "redirect_policy": "follow",
        },
    ]


def test_get_config_uses_single_site_env_when_sites_config_missing(monkeypatch):
    monkeypatch.delenv("SITES_CONFIG", raising=False)
    monkeypatch.delenv("ALERT_FAILURE_THRESHOLD", raising=False)
    monkeypatch.delenv("RETENTION_DAYS", raising=False)
    monkeypatch.setenv("TARGET_URL", "https://example.com")
    monkeypatch.setenv("SITE_ID", "my-portfolio")
    monkeypatch.setenv("TIMEOUT_SECONDS", "11")
    monkeypatch.setenv("RESPONSE_THRESHOLD_MS", "2500")
    monkeypatch.setenv("EXPECTED_TEXT", "Example Domain")
    monkeypatch.setenv("FORBIDDEN_TEXT", "")
    monkeypatch.setenv("REDIRECT_POLICY", "fail_on_redirect")

    config = get_config()

    assert config["alert_failure_threshold"] == 2
    assert config["retention_days"] == 30
    assert config["sites"] == [
        {
            "site_id": "my-portfolio",
            "target_url": "https://example.com",
            "timeout_seconds": 11,
            "response_threshold_ms": 2500,
            "expected_text": "Example Domain",
            "forbidden_text": "",
            "redirect_policy": "fail_on_redirect",
        }
    ]


def test_build_result_marks_success_when_status_and_response_time_pass():
    result = build_result(
        site_id="my-portfolio",
        check_time="2026-04-22T10:00:00Z",
        url="https://example.com",
        status_code=200,
        response_time_ms=312,
        response_threshold_ms=3000,
        failure_reason=None,
    )

    assert result["is_success"] is True
    assert result["failure_reason"] is None


def test_build_result_marks_failure_when_status_is_not_2xx():
    result = build_result(
        site_id="my-portfolio",
        check_time="2026-04-22T10:00:00Z",
        url="https://example.com",
        status_code=500,
        response_time_ms=312,
        response_threshold_ms=3000,
        failure_reason=None,
    )

    assert result["is_success"] is False
    assert result["failure_reason"] == "HTTP status outside 200-299: 500"


def test_build_result_marks_failure_when_response_is_slow():
    result = build_result(
        site_id="my-portfolio",
        check_time="2026-04-22T10:00:00Z",
        url="https://example.com",
        status_code=200,
        response_time_ms=3500,
        response_threshold_ms=3000,
        failure_reason=None,
    )

    assert result["is_success"] is False
    assert result["failure_reason"] == "Slow response: 3500ms exceeds 3000ms threshold"


def test_build_status_payload_uses_result_fields():
    result = build_result(
        site_id="my-portfolio",
        check_time="2026-04-22T10:00:00Z",
        url="https://example.com",
        status_code=200,
        response_time_ms=312,
        response_threshold_ms=3000,
        failure_reason=None,
    )
    result["consecutive_failure_count"] = 0
    result["alert_sent"] = False
    result["alert_failure_threshold"] = 2
    result["ttl_expires_at"] = 1779444000

    payload = build_status_payload(result)

    assert payload["status"] == "UP"
    assert payload["last_checked"] == "2026-04-22T10:00:00Z"
    assert payload["ttl_expires_at"] == 1779444000
    assert payload["redirect_policy"] == "follow"
    assert payload["redirect_detected"] is False
    assert payload["recent_failures"] == []


def test_get_config_falls_back_to_default_retention_days_when_invalid(monkeypatch):
    monkeypatch.delenv("SITES_CONFIG", raising=False)
    monkeypatch.setenv("RETENTION_DAYS", "not-a-number")
    monkeypatch.setenv("TARGET_URL", "https://example.com")

    config = get_config()

    assert config["retention_days"] == 30


def test_calculate_ttl_expires_at_uses_check_time_and_retention_days():
    ttl_expires_at = calculate_ttl_expires_at("2026-05-06T10:00:00Z", 30)

    assert ttl_expires_at == 1780653600


def test_run_http_check_fails_when_redirect_policy_disallows_redirect(monkeypatch):
    class FakeOpener:
        def open(self, request, timeout):  # noqa: ARG002
            raise app.urllib.error.HTTPError(
                request.full_url,
                302,
                "Found",
                {},
                None,
            )

    monkeypatch.setattr(
        app.urllib.request,
        "build_opener",
        lambda redirect_handler: FakeOpener(),  # noqa: ARG005
    )

    check = app.run_http_check(
        "https://example.com/redirect",
        timeout_seconds=10,
        redirect_policy="fail_on_redirect",
    )

    assert check["status_code"] == 302
    assert check["failure_reason"] == "Redirect not allowed: HTTP 302"
    assert check["redirect_detected"] is True


def test_without_null_values_removes_none_values_only():
    assert without_null_values({"status_code": None, "is_success": False}) == {
        "is_success": False
    }


def test_calculate_uptime_metrics_includes_current_result():
    current_result = {
        "site_id": "example-main",
        "check_time": "2026-05-06T10:00:00Z",
        "is_success": True,
    }
    recent_items = [
        {
            "site_id": "example-main",
            "check_time": "2026-05-06T09:55:00Z",
            "is_success": True,
        },
        {
            "site_id": "example-main",
            "check_time": "2026-05-06T09:50:00Z",
            "is_success": False,
        },
    ]

    metrics = calculate_uptime_metrics(current_result, recent_items)

    assert metrics == {
        "uptime_percentage": 66.67,
        "uptime_window_checks": 3,
    }


def test_calculate_uptime_metrics_uses_same_site_only():
    current_result = {
        "site_id": "example-main",
        "check_time": "2026-05-06T10:00:00Z",
        "is_success": False,
    }
    recent_items = [
        {
            "site_id": "example-main",
            "check_time": "2026-05-06T09:55:00Z",
            "is_success": True,
        },
        {
            "site_id": "example-second",
            "check_time": "2026-05-06T09:55:00Z",
            "is_success": True,
        },
    ]

    metrics = calculate_uptime_metrics(current_result, recent_items)

    assert metrics == {
        "uptime_percentage": 50.0,
        "uptime_window_checks": 2,
    }


def test_calculate_response_time_metrics_includes_current_result():
    current_result = {
        "site_id": "example-main",
        "check_time": "2026-05-06T10:00:00Z",
        "response_time_ms": 100,
    }
    recent_items = [
        {
            "site_id": "example-main",
            "check_time": "2026-05-06T09:55:00Z",
            "response_time_ms": 200,
        },
        {
            "site_id": "example-main",
            "check_time": "2026-05-06T09:50:00Z",
            "response_time_ms": 301,
        },
    ]

    metrics = calculate_response_time_metrics(current_result, recent_items)

    assert metrics == {
        "average_response_time_ms": 200,
        "response_time_window_checks": 3,
    }


def test_calculate_response_time_metrics_uses_same_site_only():
    current_result = {
        "site_id": "example-main",
        "check_time": "2026-05-06T10:00:00Z",
        "response_time_ms": 100,
    }
    recent_items = [
        {
            "site_id": "example-main",
            "check_time": "2026-05-06T09:55:00Z",
            "response_time_ms": 200,
        },
        {
            "site_id": "example-second",
            "check_time": "2026-05-06T09:55:00Z",
            "response_time_ms": 1000,
        },
    ]

    metrics = calculate_response_time_metrics(current_result, recent_items)

    assert metrics == {
        "average_response_time_ms": 150,
        "response_time_window_checks": 2,
    }


def test_calculate_incident_metrics_counts_failed_checks_in_windows():
    current_result = {
        "site_id": "example-main",
        "check_time": "2026-05-06T10:00:00Z",
        "is_success": False,
    }
    recent_items = [
        {
            "site_id": "example-main",
            "check_time": "2026-05-06T09:00:00Z",
            "is_success": False,
        },
        {
            "site_id": "example-main",
            "check_time": "2026-05-03T10:00:00Z",
            "is_success": False,
        },
        {
            "site_id": "example-main",
            "check_time": "2026-04-28T10:00:00Z",
            "is_success": False,
        },
    ]

    metrics = calculate_incident_metrics(current_result, recent_items)

    assert metrics == {
        "incident_count_24h": 2,
        "incident_count_7d": 3,
    }


def test_calculate_incident_metrics_uses_same_site_only():
    current_result = {
        "site_id": "example-main",
        "check_time": "2026-05-06T10:00:00Z",
        "is_success": True,
    }
    recent_items = [
        {
            "site_id": "example-main",
            "check_time": "2026-05-06T09:00:00Z",
            "is_success": False,
        },
        {
            "site_id": "example-second",
            "check_time": "2026-05-06T09:00:00Z",
            "is_success": False,
        },
    ]

    metrics = calculate_incident_metrics(current_result, recent_items)

    assert metrics == {
        "incident_count_24h": 1,
        "incident_count_7d": 1,
    }


def test_calculate_consecutive_failure_count_includes_current_and_uses_same_site_only():
    current_result = {
        "site_id": "example-failed",
        "check_time": "2026-05-06T10:00:00Z",
        "is_success": False,
    }
    recent_items = [
        {
            "site_id": "example-failed",
            "check_time": "2026-05-06T09:55:00Z",
            "is_success": False,
        },
        {
            "site_id": "example-main",
            "check_time": "2026-05-06T09:54:00Z",
            "is_success": False,
        },
        {
            "site_id": "example-failed",
            "check_time": "2026-05-06T09:50:00Z",
            "is_success": True,
        },
        {
            "site_id": "example-failed",
            "check_time": "2026-05-06T09:45:00Z",
            "is_success": False,
        },
    ]

    assert calculate_consecutive_failure_count(current_result, recent_items) == 2


def test_check_site_sends_alert_only_after_failure_threshold(monkeypatch):
    published_alerts = []
    stored_results = []
    recent_results = []

    monkeypatch.setattr(
        app,
        "run_http_check",
        lambda url, timeout, redirect_policy: {
            "status_code": 404,
            "response_time_ms": 50,
            "failure_reason": "HTTP 404: Not Found",
            "response_body": "",
            "redirect_detected": False,
        },
    )
    monkeypatch.setattr(
        app,
        "get_recent_results",
        lambda table, site_id: recent_results,
    )
    monkeypatch.setattr(app, "get_recent_failures", lambda table, site_id, result: [])
    monkeypatch.setattr(
        app,
        "write_result_to_dynamodb",
        lambda table, result: stored_results.append(result),
    )
    monkeypatch.setattr(
        app,
        "publish_failure_alert",
        lambda topic_arn, result: published_alerts.append(result),
    )

    config = {
        "dynamodb_table": "website_checks",
        "sns_topic_arn": "arn:aws:sns:example",
        "alert_failure_threshold": 2,
        "retention_days": 30,
    }
    site_config = {
        "site_id": "example-failed",
        "target_url": "https://example.com/not-found-test",
        "timeout_seconds": 10,
        "response_threshold_ms": 3000,
        "expected_text": None,
        "forbidden_text": None,
        "redirect_policy": "follow",
    }

    first_check = check_site(
        config,
        site_config,
        "2026-05-06T10:00:00Z",
    )

    assert first_check["result"]["consecutive_failure_count"] == 1
    assert first_check["result"]["alert_sent"] is False
    assert published_alerts == []

    recent_results.append(
        {
            "site_id": "example-failed",
            "check_time": "2026-05-06T10:00:00Z",
            "is_success": False,
            "status_code": 404,
            "response_time_ms": 50,
        }
    )

    second_check = check_site(
        config,
        site_config,
        "2026-05-06T10:05:00Z",
    )

    result = second_check["result"]
    assert result["consecutive_failure_count"] == 2
    assert result["alert_failure_threshold"] == 2
    assert result["ttl_expires_at"] == 1780653900
    assert result["alert_sent"] is True
    assert second_check["status_payload"]["alert_sent"] is True
    assert published_alerts == [result]
    assert stored_results == [first_check["result"], result]

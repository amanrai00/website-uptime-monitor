from importlib import import_module


app = import_module("lambda.app")
build_result = app.build_result
build_status_payload = app.build_status_payload
without_null_values = app.without_null_values


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

    payload = build_status_payload(result)

    assert payload["status"] == "UP"
    assert payload["last_checked"] == "2026-04-22T10:00:00Z"
    assert payload["recent_failures"] == []


def test_without_null_values_removes_none_values_only():
    assert without_null_values({"status_code": None, "is_success": False}) == {
        "is_success": False
    }

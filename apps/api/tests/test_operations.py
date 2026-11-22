"""Production hygiene: logs without user content, request ids, error reports, rate limits."""

import io
import json
import logging

import pytest
from fastapi.testclient import TestClient

from resumeiq_api import app as app_module
from resumeiq_api.app import LIMITER, app
from resumeiq_api.observability import JsonFormatter
from resumeiq_api.ratelimit import RateLimiter, client_key, parse_limits

client = TestClient(app, raise_server_exceptions=False)
SECRET = "ZEBRA-QUOKKA-7731"  # a marker that must never reach the logs


@pytest.fixture
def logs():
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("resumeiq")
    logger.addHandler(handler)
    yield lambda: [json.loads(line) for line in stream.getvalue().splitlines()]
    logger.removeHandler(handler)


def test_request_logs_hold_no_resume_or_job_text(logs):
    resume = f"Sam Rivera\nsam@example.com\n- Built a FastAPI service for {SECRET} with Python.\n"
    client.post(
        "/v1/fit-map/upload",
        files={"resume": (f"{SECRET}.txt", resume.encode(), "text/plain")},
        data={"job_description": f"## Requirements\n- Experience with Python for {SECRET}\n"},
    )
    client.post(
        "/v1/rewrite/check", json={"text": f"Built {SECRET}", "evidence": [{"id": "E1", "text": f"Built {SECRET}."}]}
    )
    lines = logs()
    assert len(lines) == 2
    raw = json.dumps(lines)
    assert SECRET not in raw and "sam@example.com" not in raw and "Sam Rivera" not in raw
    assert {line["route"] for line in lines} == {"/v1/fit-map/upload", "/v1/rewrite/check"}
    assert all(set(line) >= {"severity", "message", "request_id", "status", "latency_ms"} for line in lines)


def test_logs_use_the_route_template_not_the_raw_path(logs):
    client.get("/v1/samples/walkthrough/fit-map?ref=abc")
    (line,) = logs()
    assert line["route"] == "/v1/samples/{sample_id}/fit-map"
    assert "abc" not in json.dumps(line)


def test_every_response_has_a_request_id_and_unsafe_ids_are_replaced():
    assert len(client.get("/health").headers["X-Request-ID"]) == 32
    assert (
        client.get("/health", headers={"X-Request-ID": "trace-abc-12345"}).headers["X-Request-ID"] == "trace-abc-12345"
    )
    replaced = client.get("/health", headers={"X-Request-ID": "<script>alert(1)</script>"}).headers["X-Request-ID"]
    assert "<" not in replaced and len(replaced) == 32


def test_a_crash_becomes_a_safe_500_and_an_error_report_without_the_message(logs):
    @app.get("/__crash_for_test")
    def crash():
        raise ValueError(f"resume text {SECRET}")

    try:
        response = client.get("/__crash_for_test")
    finally:
        app.router.routes.pop()
    assert response.status_code == 500
    assert response.json()["request_id"] == response.headers["X-Request-ID"]
    assert SECRET not in response.text
    error = next(line for line in logs() if line["severity"] == "ERROR")
    assert error["@type"].endswith("ReportedErrorEvent")
    assert error["serviceContext"]["service"] == "resumeiq-api"
    assert (
        "Traceback (most recent call last)" in error["message"] and "ValueError: [message hidden]" in error["message"]
    )
    assert SECRET not in json.dumps(error)


def test_client_key_trusts_only_the_address_cloud_run_appends():
    assert client_key("6.6.6.6, 1.2.3.4", None) == client_key("1.2.3.4", None)
    assert client_key("6.6.6.6, 1.2.3.4", None) != client_key("6.6.6.6", None)
    assert client_key("spoof, 1.2.3.4, 10.0.0.1", None, trusted_hops=2) == client_key("1.2.3.4", None)
    assert client_key(None, "9.9.9.9") == client_key("9.9.9.9", None)
    assert "1.2.3.4" not in client_key("1.2.3.4", None)  # stored only as a hash


def test_limiter_window_and_retry_after():
    limiter = RateLimiter({"check": 2})
    assert limiter.check("check", "k", now=0)[0] and limiter.check("check", "k", now=1)[0]
    allowed, remaining, retry = limiter.check("check", "k", now=2)
    assert (allowed, remaining, retry) == (False, 0, 58)
    assert limiter.check("check", "other", now=2)[0]  # other clients unaffected
    assert limiter.check("check", "k", now=60.5)[0]  # first hit left the window


def test_parse_limits_ignores_bad_values():
    assert parse_limits("fit-map=5, upload=x, nope=3") == {**parse_limits(None), "fit-map": 5}


def test_spoofed_forwarded_for_cannot_bypass_the_api_limit(monkeypatch):
    monkeypatch.setitem(LIMITER.limits, "check", 3)
    body = {"text": "Built a model.", "evidence": [{"id": "E1", "text": "Built a model."}]}
    statuses = [
        client.post("/v1/rewrite/check", json=body, headers={"X-Forwarded-For": f"10.0.0.{i}, 203.0.113.7"}).status_code
        for i in range(4)
    ]
    assert statuses == [200, 200, 200, 429]
    blocked = client.post("/v1/rewrite/check", json=body, headers={"X-Forwarded-For": "203.0.113.7"})
    assert blocked.status_code == 429 and int(blocked.headers["Retry-After"]) >= 1
    other = client.post("/v1/rewrite/check", json=body, headers={"X-Forwarded-For": "198.51.100.9"})
    assert other.status_code == 200 and other.headers["X-RateLimit-Remaining"] == "2"


def test_reads_and_health_are_never_rate_limited(monkeypatch):
    monkeypatch.setitem(LIMITER.limits, "fit-map", 1)
    assert all(client.get("/health").status_code == 200 for _ in range(5))
    assert all(client.get("/v1/samples/walkthrough/fit-map").status_code == 200 for _ in range(5))


def test_limits_come_from_the_environment(monkeypatch):
    monkeypatch.setenv("RESUMEIQ_RATE_LIMITS", "rewrite=5")
    monkeypatch.setenv("RESUMEIQ_TRUSTED_HOPS", "2")
    limiter, hops = app_module.ratelimit.from_env()
    assert limiter.limits["rewrite"] == 5 and hops == 2

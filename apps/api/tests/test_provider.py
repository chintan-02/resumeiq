"""The model client: request shape, provider errors, and that failures are visible but safe."""

import io
import json
import logging
import sys
import urllib.error
from pathlib import Path

from fastapi.testclient import TestClient

from resumeiq_api import rewrite as rw
from resumeiq_api.rewrite import DailyBudget, EvidenceLine, ProviderError, anthropic_completion, rewrite

REPO = Path(__file__).resolve().parents[3]
EVIDENCE = [EvidenceLine("E1", "Contributed to deploying the churn model to AWS with the platform team.")]
SECRET = "ZEBRA-QUOKKA-7731"


class _Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _capture(monkeypatch, reply: dict | None = None, error: urllib.error.HTTPError | None = None) -> list[dict]:
    sent: list[dict] = []

    def fake_urlopen(request, timeout):
        sent.append(json.loads(request.data))
        if error is not None:
            raise error
        return _Response(json.dumps(reply).encode())

    monkeypatch.setattr(rw.urllib.request, "urlopen", fake_urlopen)
    return sent


def test_temperature_is_not_sent_unless_configured(monkeypatch):
    sent = _capture(monkeypatch, {"content": [{"type": "text", "text": '{"bullet": "ok"}'}]})
    anthropic_completion("k", "claude-haiku-5-5")("system", "user")
    anthropic_completion("k", "claude-haiku-5-5", temperature=0.3)("system", "user")
    assert "temperature" not in sent[0]
    assert sent[1]["temperature"] == 0.3


def test_configured_temperature_reads_the_environment(monkeypatch):
    monkeypatch.delenv("RESUMEIQ_LLM_TEMPERATURE", raising=False)
    assert rw.configured_temperature() is None
    monkeypatch.setenv("RESUMEIQ_LLM_TEMPERATURE", "0.4")
    assert rw.configured_temperature() == 0.4
    monkeypatch.setenv("RESUMEIQ_LLM_TEMPERATURE", "warm")
    assert rw.configured_temperature() is None


def test_http_errors_become_provider_errors_with_safe_fields(monkeypatch):
    body = {
        "type": "error",
        "error": {"type": "invalid_request_error", "message": "`temperature` is deprecated"},
        "request_id": "req_123",
    }
    error = urllib.error.HTTPError("https://api", 400, "Bad Request", {}, io.BytesIO(json.dumps(body).encode()))
    _capture(monkeypatch, error=error)
    try:
        anthropic_completion("k", "m")("s", "u")
    except ProviderError as failure:
        assert (failure.status, failure.error_type, failure.request_id) == (400, "invalid_request_error", "req_123")
    else:
        raise AssertionError("expected ProviderError")


def test_a_failed_call_is_logged_without_content_and_falls_back(caplog):
    def failing(system, user):
        raise ProviderError(400, "invalid_request_error", "req_abc")

    logger = logging.getLogger("resumeiq")
    logger.addHandler(caplog.handler)
    try:
        trace: list[dict] = []
        evidence = [EvidenceLine("E1", f"Contributed to deploying {SECRET} to AWS with the platform team.")]
        result = rewrite("Lead deployments", evidence, failing, DailyBudget(5), trace=trace)
    finally:
        logger.removeHandler(caplog.handler)
    assert result.source == "rules" and result.check.passed
    assert trace == [{"attempt": 1, "error": "400 invalid_request_error"}]
    record = next(r for r in caplog.records if "Model call failed" in r.getMessage())
    assert record.fields["status"] == 400 and record.fields["provider_request_id"] == "req_abc"
    assert SECRET not in json.dumps(record.fields) and SECRET not in record.getMessage()


def test_status_reports_the_model(monkeypatch):
    from resumeiq_api import app as app_module

    monkeypatch.setattr(app_module, "COMPLETE", lambda s, u: "")
    monkeypatch.setenv("RESUMEIQ_LLM_MODEL", "claude-haiku-5-5")
    body = TestClient(app_module.app).get("/v1/rewrite/status").json()
    assert body["model_enabled"] is True and body["model"] == "claude-haiku-5-5"


def test_drafting_eval_refuses_to_write_a_report_when_every_call_fails(tmp_path, capsys):
    sys.path.insert(0, str(REPO / "evals"))
    import run_drafting_eval

    def failing(system, user):
        raise ProviderError(400, "invalid_request_error", None)

    assert run_drafting_eval.run(failing, "m", tmp_path, fake=False) == 1
    assert not (tmp_path / "REPORT.md").exists()
    assert "400 invalid_request_error" in capsys.readouterr().out


def test_thinking_is_disabled_by_default_and_can_be_omitted(monkeypatch):
    sent = _capture(monkeypatch, {"content": [{"type": "text", "text": '{"bullet": "ok"}'}]})
    anthropic_completion("k", "m")("s", "u")
    anthropic_completion("k", "m", thinking=None)("s", "u")
    assert sent[0]["thinking"] == {"type": "disabled"} and sent[0]["max_tokens"] == rw.MAX_OUTPUT_TOKENS
    assert "thinking" not in sent[1]
    monkeypatch.setenv("RESUMEIQ_LLM_THINKING", "omit")
    assert rw.configured_thinking() is None
    monkeypatch.delenv("RESUMEIQ_LLM_THINKING")
    assert rw.configured_thinking() == "disabled"


def test_a_reply_without_text_is_an_empty_reply_logged_with_its_stop_reason(monkeypatch, caplog):
    _capture(monkeypatch, {"content": [{"type": "thinking", "thinking": ""}], "stop_reason": "max_tokens"})
    complete = anthropic_completion("k", "m")
    logger = logging.getLogger("resumeiq")
    logger.addHandler(caplog.handler)
    try:
        trace: list[dict] = []
        result = rewrite("Lead deployments", EVIDENCE, complete, DailyBudget(5), trace=trace)
    finally:
        logger.removeHandler(caplog.handler)
    assert result.source == "rules"
    assert trace == [{"attempt": 1, "error": "empty reply (stop_reason=max_tokens)"}]
    record = next(r for r in caplog.records if "Model call failed" in r.getMessage())
    assert record.fields["stop_reason"] == "max_tokens" and record.fields["error"] == "EmptyReply"


def test_drafting_eval_refuses_when_many_first_calls_fail(tmp_path, capsys):
    sys.path.insert(0, str(REPO / "evals"))
    import run_drafting_eval

    calls = {"n": 0}

    def mostly_empty(system, user):
        calls["n"] += 1
        if calls["n"] % 3:
            raise rw.EmptyReply("max_tokens")
        return '{"bullet": "Built a model, [add measurable result]"}'

    assert run_drafting_eval.run(mostly_empty, "m", tmp_path, fake=False) == 1
    assert not (tmp_path / "REPORT.md").exists()
    assert "empty reply (stop_reason=max_tokens)" in capsys.readouterr().out

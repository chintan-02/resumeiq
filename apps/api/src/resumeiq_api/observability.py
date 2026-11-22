"""Structured request logs and error reports, safe for resume data.

Cloud Run sends each JSON line on stdout to Cloud Logging, which reads `severity`
and `message`. Lines with severity ERROR and a stack trace, tagged as a
ReportedErrorEvent, are grouped by Cloud Error Reporting, so error tracking needs no
extra service or SDK.

What a log line may contain: request id, method, the route *template*
(`/v1/samples/{sample_id}/fit-map`, never the raw URL), status, latency and the
trace id. What it never contains: request or response bodies, query strings, file
names, IP addresses or user agents. Resumes and job descriptions only ever travel
in bodies, so they cannot reach the logs through this module.
"""

from __future__ import annotations

import json
import logging
import re
import sys
import time
import traceback
import uuid
from datetime import UTC, datetime

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.routing import Match

from . import __version__

SERVICE = "resumeiq-api"
_SAFE_ID = re.compile(r"^[A-Za-z0-9_-]{8,64}$")
_ERROR_TYPE = "type.googleapis.com/google.devtools.clouderrorreporting.v1beta1.ReportedErrorEvent"

log = logging.getLogger("resumeiq")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "time": datetime.fromtimestamp(record.created, UTC).isoformat(),
        }
        entry.update(getattr(record, "fields", {}))
        return json.dumps(entry, ensure_ascii=False)


def configure_logging() -> None:
    if any(isinstance(h.formatter, JsonFormatter) for h in log.handlers):
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    log.addHandler(handler)
    log.setLevel(logging.INFO)
    log.propagate = False


def _route_template(request: Request) -> str:
    for route in request.app.router.routes:
        match, _ = route.matches(request.scope)
        if match is Match.FULL:
            return getattr(route, "path", "unmatched")
    return "unmatched"


def _trace_id(request: Request) -> str | None:
    header = request.headers.get("x-cloud-trace-context", "")
    trace = header.split("/", 1)[0]
    return trace if re.fullmatch(r"[0-9a-fA-F]{32}", trace) else None


def request_id_for(request: Request) -> str:
    incoming = request.headers.get("x-request-id", "")
    return incoming if _SAFE_ID.match(incoming) else uuid.uuid4().hex


def install(app: FastAPI) -> None:
    """Request logging, request ids on every response, and error reports for crashes."""
    configure_logging()

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        request_id = request_id_for(request)
        request.state.request_id = request_id
        start = time.perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
        except Exception as error:  # noqa: BLE001 - reported, then answered with a safe 500
            report_error(error, request, request_id)
            response = JSONResponse(
                {"detail": f"Something went wrong on our side (reference {request_id[:8]}).", "request_id": request_id},
                status_code=500,
            )
        latency_ms = round((time.perf_counter() - start) * 1000, 1)
        response.headers["X-Request-ID"] = request_id
        fields = {
            "request_id": request_id,
            "method": request.method,
            "route": _route_template(request),
            "status": status,
            "latency_ms": latency_ms,
        }
        if trace := _trace_id(request):
            fields["trace_id"] = trace
        level = logging.WARNING if status >= 500 else logging.INFO
        log.log(level, f"{request.method} {fields['route']} {status}", extra={"fields": fields})
        return response


def report_error(error: BaseException, request: Request, request_id: str) -> None:
    """One ERROR line that Cloud Error Reporting groups by stack trace."""
    # Frames show where it failed; the exception message is dropped because it could
    # quote user input. The format is what Error Reporting expects from Python.
    frames = "".join(traceback.format_tb(error.__traceback__))
    stack = f"Traceback (most recent call last):\n{frames}{type(error).__name__}: [message hidden]"
    log.error(
        stack,
        extra={
            "fields": {
                "@type": _ERROR_TYPE,
                "serviceContext": {"service": SERVICE, "version": __version__},
                "context": {"httpRequest": {"method": request.method, "url": _route_template(request)}},
                "request_id": request_id,
            }
        },
    )

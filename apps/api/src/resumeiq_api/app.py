"""ResumeIQ API.

Requirement extraction and matching are local and rule-based, so they cost
nothing per request. The only model call is bullet drafting (rewrite.py). It is
off unless ANTHROPIC_API_KEY is set, and a daily call budget is checked here
before every provider request. Uploaded resumes are parsed in memory, masked for
contact details and never stored.
"""

from __future__ import annotations

import json
import os
from typing import Annotated, Literal

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from . import __version__, observability, ratelimit
from .fitmap import build_fit_map, tuned_matcher
from .models import FitMap, Level, SourceDocument
from .models import Requirement as RequirementModel
from .requirements import MAX_JD_CHARS, MAX_REQUIREMENT_CHARS, MAX_REQUIREMENTS
from .rewrite import DailyBudget, EvidenceLine, check_claim, configured_completion, rewrite
from .samples import load_samples
from .uploads import MAX_UPLOAD_BYTES, UploadError, read_resume

app = FastAPI(title="ResumeIQ API", version=__version__)
SAMPLES = load_samples()
COMPLETE = configured_completion()
BUDGET = DailyBudget(int(os.environ.get("RESUMEIQ_REWRITE_DAILY_LIMIT", "40")))
LIMITER, TRUSTED_HOPS = ratelimit.from_env()

# POST routes and their limit buckets. Checked before the body is read, so an
# over-limit upload is refused without reading the file.
LIMITED = {
    "/v1/fit-map": "fit-map",
    "/v1/fit-map/upload": "upload",
    "/v1/rewrite": "rewrite",
    "/v1/rewrite/check": "check",
}


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    bucket = LIMITED.get(request.url.path) if request.method == "POST" else None
    if bucket is None:
        return await call_next(request)
    key = ratelimit.client_key(
        request.headers.get("x-forwarded-for"), request.client and request.client.host, TRUSTED_HOPS
    )
    allowed, remaining, retry_after = LIMITER.check(bucket, key)
    if not allowed:
        return JSONResponse(
            {"detail": "Too many requests. Wait a minute and try again."},
            status_code=429,
            headers={"Retry-After": str(retry_after), "X-RateLimit-Remaining": "0"},
        )
    response = await call_next(request)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    return response


# Added last, so it wraps everything above: 429s and crashes are logged too.
observability.install(app)


class RequirementIn(BaseModel):
    text: str = Field(min_length=3, max_length=MAX_REQUIREMENT_CHARS)
    priority: Literal["must", "nice"] = "must"
    required_level: Level | None = None


class FitMapRequest(BaseModel):
    sample_id: str = Field(default="walkthrough", max_length=40)
    job_title: str | None = Field(default=None, max_length=120)
    job_description: str | None = Field(default=None, max_length=MAX_JD_CHARS)
    requirements: list[RequirementIn] | None = Field(default=None, max_length=MAX_REQUIREMENTS)
    matcher: Literal["keyword-rules-v2", "keyword-rules", "keyword"] = "keyword-rules-v2"


@app.get("/health")
@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@app.get("/v1/samples")
def list_samples() -> list[dict]:
    return [
        {
            "id": s.id,
            "title": s.title,
            "job_title": s.job_title,
            "documents": [{"id": d.id, "kind": d.kind, "title": d.title} for d in s.documents],
        }
        for s in SAMPLES.values()
    ]


@app.get("/v1/samples/{sample_id}/documents")
def sample_documents(sample_id: str) -> list[dict]:
    sample = _sample(sample_id)
    return [d.model_dump() for d in sample.documents]


@app.get("/v1/samples/{sample_id}/fit-map", response_model=FitMap)
def precomputed_fit_map(sample_id: str) -> JSONResponse:
    """The committed walkthrough result: available even if live matching is down."""
    sample = _sample(sample_id)
    return JSONResponse(json.loads(sample.precomputed_path.read_text(encoding="utf-8")))


@app.post("/v1/fit-map", response_model=FitMap)
def fit_map(request: FitMapRequest) -> FitMap:
    sample = _sample(request.sample_id)
    requirements = None
    if request.requirements is not None:
        from .levels import required_level

        requirements = [
            RequirementModel(
                id=f"R{i + 1:02d}",
                text=r.text.strip(),
                priority=r.priority,
                required_level=r.required_level if r.required_level is not None else required_level(r.text),
            )
            for i, r in enumerate(request.requirements)
        ]
    job_text = request.job_description if request.job_description is not None else sample.job_text
    job_title = request.job_title or ("Custom job description" if request.job_description else sample.job_title)
    return build_fit_map(
        documents=sample.documents,
        job_title=job_title,
        job_text=job_text,
        requirements=requirements,
        matcher=tuned_matcher(request.matcher),
    )


class UploadFitMapResponse(BaseModel):
    documents: list[SourceDocument]
    fit_map: FitMap


@app.post("/v1/fit-map/upload", response_model=UploadFitMapResponse)
async def fit_map_from_upload(
    resume: Annotated[UploadFile, File()],
    job_description: Annotated[str, Form(max_length=MAX_JD_CHARS)],
) -> UploadFitMapResponse:
    """Fit map for an uploaded resume. The file is read in memory and never stored."""
    data = await resume.read(MAX_UPLOAD_BYTES + 1)
    try:
        text = read_resume(resume.filename or "", data)
    except UploadError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    finally:
        del data
    documents = [SourceDocument(id="RES", kind="resume", title="Your resume", text=text)]
    fit = build_fit_map(documents=documents, job_title="Your job description", job_text=job_description)
    return UploadFitMapResponse(documents=documents, fit_map=fit)


class EvidenceIn(BaseModel):
    id: str = Field(max_length=40)
    text: str = Field(min_length=3, max_length=400)


class RewriteRequest(BaseModel):
    requirement: str = Field(min_length=3, max_length=MAX_REQUIREMENT_CHARS)
    evidence: list[EvidenceIn] = Field(min_length=1, max_length=3)


class CheckRequest(BaseModel):
    text: str = Field(max_length=600)
    evidence: list[EvidenceIn] = Field(min_length=1, max_length=3)


class CheckOut(BaseModel):
    passed: bool
    issues: list[str]
    approval_token: str | None


class RewriteOut(BaseModel):
    bullet: str
    source: Literal["model", "rules"]
    check: CheckOut


@app.get("/v1/rewrite/status")
def rewrite_status() -> dict:
    return {"model_enabled": COMPLETE is not None, "remaining_today": BUDGET.remaining() if COMPLETE else 0}


@app.post("/v1/rewrite", response_model=RewriteOut)
def draft_bullet(request: RewriteRequest) -> RewriteOut:
    lines = [EvidenceLine(e.id, e.text) for e in request.evidence]
    result = rewrite(request.requirement, lines, COMPLETE, BUDGET)
    check = result.check
    return RewriteOut(
        bullet=result.bullet,
        source=result.source,  # type: ignore[arg-type]
        check=CheckOut(passed=check.passed, issues=check.issues, approval_token=check.token),
    )


@app.post("/v1/rewrite/check", response_model=CheckOut)
def check_bullet(request: CheckRequest) -> CheckOut:
    """Re-check an edited bullet. Approval needs the token this returns for the exact text."""
    check = check_claim(request.text, [EvidenceLine(e.id, e.text) for e in request.evidence])
    return CheckOut(passed=check.passed, issues=check.issues, approval_token=check.token)


def _sample(sample_id: str):
    sample = SAMPLES.get(sample_id)
    if sample is None:
        raise HTTPException(status_code=404, detail="Sample not found.")
    return sample

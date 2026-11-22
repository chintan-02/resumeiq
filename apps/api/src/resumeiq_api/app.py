"""ResumeIQ v2 API, Milestone 1.

No model calls happen here: requirement extraction and matching are local and
rule-based, so the demo costs nothing per request and keeps working when no AI
provider is available. When an LLM step is added, a global spend budget must be
checked in this backend before any provider call (see docs/v2/MILESTONE_1.md).
"""

from __future__ import annotations

import json
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from . import __version__
from .fitmap import build_fit_map, tuned_matcher
from .models import FitMap, Level
from .models import Requirement as RequirementModel
from .requirements import MAX_JD_CHARS, MAX_REQUIREMENT_CHARS, MAX_REQUIREMENTS
from .samples import load_samples

app = FastAPI(title="ResumeIQ API", version=__version__)
SAMPLES = load_samples()


class RequirementIn(BaseModel):
    text: str = Field(min_length=3, max_length=MAX_REQUIREMENT_CHARS)
    priority: Literal["must", "nice"] = "must"
    required_level: Level | None = None


class FitMapRequest(BaseModel):
    sample_id: str = Field(default="walkthrough", max_length=40)
    job_title: str | None = Field(default=None, max_length=120)
    job_description: str | None = Field(default=None, max_length=MAX_JD_CHARS)
    requirements: list[RequirementIn] | None = Field(default=None, max_length=MAX_REQUIREMENTS)
    matcher: Literal["keyword-rules", "keyword"] = "keyword-rules"


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


def _sample(sample_id: str):
    sample = SAMPLES.get(sample_id)
    if sample is None:
        raise HTTPException(status_code=404, detail="Sample not found.")
    return sample

"""Assemble a fit map: requirements × evidence → status + exact source quotes."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

from .evidence import segment
from .matching import Matcher, Thresholds, build_matcher
from .models import Coverage, EvidenceItem, FitMap, FitMapSummary, Requirement, SourceDocument
from .requirements import extract_requirements

DEFAULT_MATCHER = "keyword-rules-v4"
TUNED_THRESHOLDS_PATH = Path(__file__).with_name("tuned_thresholds.json")


def tuned_matcher(name: str) -> Matcher:
    """Matcher with thresholds tuned on the dev split, if a tuning run has been committed."""
    if TUNED_THRESHOLDS_PATH.exists():
        tuned = json.loads(TUNED_THRESHOLDS_PATH.read_text(encoding="utf-8"))
        if name in tuned:
            return build_matcher(name, Thresholds(**tuned[name]))
    return build_matcher(name)


def build_fit_map(
    documents: Sequence[SourceDocument],
    job_title: str,
    job_text: str | None = None,
    requirements: Sequence[Requirement] | None = None,
    matcher: Matcher | None = None,
) -> FitMap:
    """Build a fit map from documents and either a job description or edited requirements."""
    matcher = matcher or tuned_matcher(DEFAULT_MATCHER)
    warnings: list[str] = []
    ignored: list[str] = []
    if requirements is None:
        extraction = extract_requirements(job_text or "")
        requirements = extraction.requirements
        warnings += extraction.warnings
        ignored = extraction.ignored_lines

    strict = matcher.name == DEFAULT_MATCHER
    evidence: list[EvidenceItem] = [
        item for doc in documents for item in segment(doc, preserve_bullets=strict and doc.kind == "resume")
    ]
    # Only confirmed evidence feeds matching (unconfirmed items are shown for review only).
    usable = [item for item in evidence if item.confirmed]

    results = [matcher.match(req, usable) for req in requirements]
    must = [r for r in results if r.requirement.priority == "must"]
    summary = FitMapSummary(
        supported=sum(r.status is Coverage.SUPPORTED for r in results),
        partial=sum(r.status is Coverage.PARTIAL for r in results),
        not_found=sum(r.status is Coverage.NOT_FOUND for r in results),
        must_have_supported=sum(r.status is Coverage.SUPPORTED for r in must),
        must_have_total=len(must),
    )
    from .health import check_resume  # local imports: both modules depend on matching
    from .tailor import build_actions

    posting = job_text if job_text else "\n".join(r.text for r in requirements)
    resume = next((d for d in documents if d.kind == "resume"), None)
    return FitMap(
        job_title=job_title,
        matcher=matcher.name,
        results=results,
        summary=summary,
        warnings=warnings,
        ignored_lines=ignored,
        actions=build_actions(results, usable, documents, posting, strict=strict),
        health=check_resume(resume) if resume else [],
    )

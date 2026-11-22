"""Typed data shapes shared by the domain logic, the matchers and the API.

Every quote the system returns is a slice of a source document identified by
character offsets, so the UI can always show exactly where a claim came from.
"""

from __future__ import annotations

from enum import IntEnum, StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class Level(IntEnum):
    """How strongly a requirement asks for, or evidence shows, a skill.

    See evals/LABELING_GUIDE.md for the definitions.
    """

    NONE = 0
    AWARE = 1
    USED = 2
    BUILT = 3
    OWNED = 4


class Coverage(StrEnum):
    SUPPORTED = "supported"
    PARTIAL = "partial"
    NOT_FOUND = "not_found"


class SourceDocument(BaseModel):
    id: str
    kind: Literal["resume", "writeup"]
    title: str
    text: str


class EvidenceItem(BaseModel):
    """One sentence or bullet from a source document, located by offsets."""

    id: str
    document_id: str
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    text: str
    level: Level
    confirmed: bool = True


class Requirement(BaseModel):
    id: str
    text: str = Field(min_length=3, max_length=300)
    priority: Literal["must", "nice"] = "must"
    required_level: Level = Level.USED


class Citation(BaseModel):
    evidence_id: str
    document_id: str
    start: int
    end: int
    quote: str
    level: Level
    score: float


class RequirementResult(BaseModel):
    requirement: Requirement
    status: Coverage
    reason: str
    citations: list[Citation] = []
    candidates: list[str] = Field(
        default=[], description="Evidence ids ranked by the matcher, best first (for recall@k)."
    )


class FitMapSummary(BaseModel):
    supported: int
    partial: int
    not_found: int
    must_have_supported: int
    must_have_total: int


class ActionKind(StrEnum):
    MISSING = "missing"  # nothing in the documents mentions it
    LISTED_NOT_SHOWN = "listed_not_shown"  # named in a skills list, never shown in use
    LEARNED_NOT_USED = "learned_not_used"  # course, reading or training only
    BELOW_LEVEL = "below_level"  # shown, but weaker than the job asks ("contributed" vs "lead")
    PARTIAL_COVERAGE = "partial_coverage"  # some components shown, others not
    WORDING = "wording"  # same skill, different name from the posting ("Postgres" vs "PostgreSQL")
    ADD_RESULT = "add_result"  # backed, but the line has no measurable result


class Action(BaseModel):
    """One concrete step to tailor the resume to this job. Never invents content."""

    id: str
    kind: ActionKind
    priority: Literal[1, 2, 3] = Field(description="1 = must-have gap, 2 = wording or nice-to-have, 3 = polish")
    requirement_id: str | None = None
    title: str
    detail: str
    terms: list[str] = []
    citations: list[Citation] = Field(default=[], description="Lines this action is about, with exact offsets.")
    suggestion: str | None = Field(default=None, description="A bullet shape with [placeholders] to fill truthfully.")


class HealthCheck(BaseModel):
    """A pass/warn result for one resume-wide check. There is deliberately no overall score."""

    id: str
    label: str
    status: Literal["pass", "warn"]
    detail: str
    items: list[str] = []


class FitMap(BaseModel):
    job_title: str
    matcher: str
    results: list[RequirementResult]
    summary: FitMapSummary
    warnings: list[str] = []
    ignored_lines: list[str] = Field(
        default=[], description="Job-description lines dropped because they look like instructions."
    )
    actions: list[Action] = Field(default=[], description="Tailor plan, most important first.")
    health: list[HealthCheck] = Field(default=[], description="Resume-wide checks for the resume document.")

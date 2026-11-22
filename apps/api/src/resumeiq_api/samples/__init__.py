"""Synthetic walkthrough samples for the public demo.

These samples exist to show the workflow end to end. They are never part of the
evaluation set (a test enforces this), so demo polish cannot inflate reported quality.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..models import SourceDocument

SAMPLES_DIR = Path(__file__).parent


@dataclass(frozen=True)
class Sample:
    id: str
    title: str
    job_title: str
    documents: tuple[SourceDocument, ...]
    job_text: str
    precomputed_path: Path


def _read(name: str) -> str:
    return (SAMPLES_DIR / "walkthrough" / name).read_text(encoding="utf-8")


def _first_heading(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return "Untitled"


def load_samples() -> dict[str, Sample]:
    resume, writeup, job = _read("resume.md"), _read("writeup.md"), _read("job.md")
    walkthrough = Sample(
        id="walkthrough",
        title="Jordan Avery (synthetic) · Applied ML Engineer",
        job_title=_first_heading(job),
        documents=(
            SourceDocument(id="RES", kind="resume", title="Resume (synthetic)", text=resume),
            SourceDocument(id="WRT", kind="writeup", title="Project write-up (synthetic)", text=writeup),
        ),
        job_text=job,
        precomputed_path=SAMPLES_DIR / "walkthrough" / "fitmap.json",
    )
    return {walkthrough.id: walkthrough}

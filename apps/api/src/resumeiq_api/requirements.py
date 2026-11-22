"""Extract requirements from a pasted job description.

Job descriptions are untrusted input. This extractor is rule-based, so text in a
job description can never change the response format or the matching logic.
Lines that look like instructions to an AI system are dropped and reported back,
so the UI can show the user what was ignored.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .levels import required_level
from .models import Requirement

MAX_JD_CHARS = 12_000
MAX_REQUIREMENTS = 30
MAX_REQUIREMENT_CHARS = 300

_BULLET = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s+(.*\S)\s*$")
_HEADING = re.compile(r"^\s*(?:#{1,6}\s*(.+?)|\*\*(.+?)\*\*|([A-Za-z][^.!?]{0,60}):)\s*$")
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

_NICE = re.compile(r"nice to have|bonus|preferred|assets?\b|\bplus\b|good to have", re.I)
_MUST = re.compile(
    r"requirement|qualification|what you('|’)?ll bring|what you bring|you have|"
    r"must have|minimum|skills|what we('|’)?re looking for",
    re.I,
)

_INSTRUCTION_LIKE = [
    r"\bignore (all |any )?(the )?(previous|prior|above|earlier) (instructions|text|rules)",
    r"\bdisregard (all |any )?(the )?(previous|prior|above|earlier)",
    r"\bsystem prompt\b",
    r"^\s*(system|assistant|developer)\s*:",
    r"\byou are (now )?(an?|the) (ai|assistant|model|language model)\b",
    r"\bmark (every|all|each)\b.*\b(supported|covered|matched)\b",
    r"\bcite\b.*\b[A-Z]{1,3}\d*-E\d+",
    r"<\s*/?\s*(script|system|instructions?)\b",
    r"\boverride\b.*\b(rules|instructions|status|review)\b",
    r"\bskip (the )?(review|verification|approval)\b",
]


@dataclass
class Extraction:
    requirements: list[Requirement] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    ignored_lines: list[str] = field(default_factory=list)


def looks_like_instruction(line: str) -> bool:
    return any(re.search(p, line, flags=re.I) for p in _INSTRUCTION_LIKE)


def _section_kind(heading: str) -> str | None:
    if _NICE.search(heading):
        return "nice"
    if _MUST.search(heading):
        return "must"
    return None


def extract_requirements(job_text: str) -> Extraction:
    if len(job_text) > MAX_JD_CHARS:
        raise ValueError(f"Job description is longer than {MAX_JD_CHARS} characters.")
    text = _CONTROL.sub("", job_text)
    result = Extraction()
    section: str | None = None
    saw_section = False
    loose_bullets: list[str] = []

    for line in text.splitlines():
        if not line.strip():
            continue
        if looks_like_instruction(line):
            result.ignored_lines.append(line.strip()[:MAX_REQUIREMENT_CHARS])
            continue
        heading = _HEADING.match(line)
        bullet = _BULLET.match(line)
        if heading and not bullet:
            title = next(g for g in heading.groups() if g)
            section = _section_kind(title)
            saw_section = saw_section or section is not None
            continue
        if not bullet:
            continue
        item = bullet.group(1)
        if section is None:
            loose_bullets.append(item)
            continue
        _add(result, item, section)

    if not saw_section and loose_bullets:
        result.warnings.append(
            "No requirements heading found; every bullet was treated as a must-have. Check the list."
        )
        for item in loose_bullets:
            _add(result, item, "must")

    if result.ignored_lines:
        result.warnings.append(
            f"{len(result.ignored_lines)} line(s) looked like instructions to an AI system and were ignored."
        )
    if not result.requirements:
        result.warnings.append("No requirements found. Paste the requirements list or add them by hand.")
    return result


def _add(result: Extraction, item: str, priority: str) -> None:
    if len(result.requirements) >= MAX_REQUIREMENTS:
        if not any("first" in w for w in result.warnings):
            result.warnings.append(f"Only the first {MAX_REQUIREMENTS} requirements were kept.")
        return
    text = item.strip()
    if len(text) > MAX_REQUIREMENT_CHARS:
        text = text[:MAX_REQUIREMENT_CHARS].rsplit(" ", 1)[0]
        result.warnings.append("A very long requirement was shortened.")
    if len(text) < 3:
        return
    result.requirements.append(
        Requirement(
            id=f"R{len(result.requirements) + 1:02d}",
            text=text,
            priority=priority,  # type: ignore[arg-type]
            required_level=required_level(text),
        )
    )

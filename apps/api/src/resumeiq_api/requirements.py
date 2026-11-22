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

_BULLET = re.compile(r"^\s*(?:[-*•·▪◦●–—✓✔➢►]|\d{1,2}[.)])\s+(.*\S)\s*$")
# "What You'll Do1. Design X.2. Own Y." — numbered lists flattened by copy-paste.
_INLINE_NUMBER = re.compile(r"(?<=[A-Za-z.;:)’'\"])\s*(\d{1,2})[.)]\s+(?=[A-Z0-9])")
_INLINE_BULLET = re.compile(r"\s*[•·▪●]\s*")
_SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")
_MIN_ITEM_CHARS = 12
_HEADING = re.compile(r"^\s*(?:#{1,6}\s*(.+?)|\*\*(.+?)\*\*|([A-Za-z][^.!?]{0,60}):)\s*$")
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

_NICE = re.compile(r"nice to have|bonus|preferred|assets?\b|\bplus(es)?\b|good to have", re.I)
_SKIP = re.compile(
    r"^(about (us|the company|the team|the role|the job|\w+)|benefits|perks|what we offer|"
    r"compensation|salary|pay( range)?|equal opportunity|eeo|how to apply|location|"
    r"our (values|culture|mission|story)|why join|life at|overview|the role|job description)\b",
    re.I,
)
_MUST = re.compile(
    r"requirement|qualification|what you('|’)?ll bring|what you bring|you have|you('|’)?ll have|"
    r"must have|minimum|skills|what we('|’)?re looking for|who you are|about you|experience|"
    r"what you('|’)?ll do|what you will do|responsibilit|your role|in this role|day to day",
    re.I,
)
# A plain line that is exactly a known section name, with no markdown or colon.
_BARE_HEADING = re.compile(
    r"^(?:(?:key|core|main|basic|minimum|required|preferred|additional|desired|bonus|your|the|our)\s+)*"
    r"(?:requirements?|qualifications?|responsibilities|duties|skills(?: (?:and|&) (?:experience|qualifications))?|"
    r"experience|must[- ]haves?|nice[- ]to[- ]haves?|good[- ]to[- ]haves?|bonus(?: points)?|pluses|assets?|"
    r"what you(?:'|’)?ll (?:do|bring|need|have)|what you will (?:do|bring|need)|what you bring|"
    r"what we(?:'|’)?re looking for|what we are looking for|who you are|about you|you have|"
    r"you(?:'|’)?ll have|in this role(?:,? you will)?|the role|role|day[- ]to[- ]day|"
    r"about (?:us|the company|the team|the role|the job|[\w.&-]+)|benefits|perks|what we offer|"
    r"compensation|salary|pay range|equal opportunity(?: employer)?|how to apply|location|"
    r"our (?:values|culture|mission|story)|why join(?: us)?|overview|job description)$",
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


# Pay, benefits and hiring-policy text often sits inside a requirements section
# when a posting is pasted without its own headings. It is not a requirement.
_BOILERPLATE = [
    r"\$\s?\d",
    r"\b(base )?salary\b",
    r"\bpay range\b",
    r"\bcompensation\b",
    r"\b401\s?\(?k\)?",
    r"\bpaid time off\b|\bPTO\b",
    r"\bhealth[- ]insurance\b|\bdental\b",
    r"\beligible for (equity|bonus)",
    r"\bequal (employment )?opportunity\b",
    r"\bqualified applicants\b",
    r"\bwithout regard to\b",
    r"\breasonable accommodation",
    r"\bprotected (veteran|characteristic|status)",
    r"\bhiring process\b",
    r"\bcandidate screening\b",
    r"\bvisa sponsorship\b|\bbackground check\b|\be-?verify\b",
]


def looks_like_boilerplate(line: str) -> bool:
    return any(re.search(p, line, flags=re.I) for p in _BOILERPLATE)


@dataclass
class Extraction:
    requirements: list[Requirement] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    ignored_lines: list[str] = field(default_factory=list)


def looks_like_instruction(line: str) -> bool:
    return any(re.search(p, line, flags=re.I) for p in _INSTRUCTION_LIKE)


def _section_kind(heading: str) -> str | None:
    heading = heading.strip().rstrip(":").strip()
    if _NICE.search(heading):
        return "nice"
    if _SKIP.search(heading):
        return None
    if _MUST.search(heading):
        return "must"
    return None


def _bare_heading(line: str) -> str | None:
    """A plain line such as "Qualifications" or "What You'll Do" names a section."""
    text = line.strip().rstrip(":").strip()
    return text if _BARE_HEADING.match(text) else None


def _split_flattened_lists(line: str) -> list[str]:
    """Undo copy-paste flattening of numbered or dotted lists into one line."""
    matches = list(_INLINE_NUMBER.finditer(line))
    numbers = [int(m.group(1)) for m in matches]
    if any(b == a + 1 for a, b in zip(numbers, numbers[1:], strict=False)):
        parts, start = [], 0
        for m in matches:
            parts.append(line[start : m.start()])
            start = m.start(1)
        parts.append(line[start:])
        return [p for p in (part.strip() for part in parts) if p]
    if len(_INLINE_BULLET.findall(line)) >= 2:
        head, *items = _INLINE_BULLET.split(line)
        return ([head.strip()] if head.strip() else []) + [f"- {i.strip()}" for i in items if i.strip()]
    return [line]


def _plain_items(line: str) -> list[str]:
    """Unbulleted lines inside a requirements section; long paragraphs split into sentences."""
    text = line.strip()
    pieces = _SENTENCE.split(text) if len(text) > MAX_REQUIREMENT_CHARS else [text]
    return [p.strip() for p in pieces if len(p.strip()) >= _MIN_ITEM_CHARS]


def extract_requirements(job_text: str) -> Extraction:
    if len(job_text) > MAX_JD_CHARS:
        raise ValueError(f"Job description is longer than {MAX_JD_CHARS} characters.")
    text = _CONTROL.sub("", job_text)
    result = Extraction()
    section: str | None = None
    saw_section = False
    loose_bullets: list[str] = []

    lines = [part for raw in text.splitlines() for part in _split_flattened_lists(raw)]
    skipped_boilerplate = 0
    for line in lines:
        if not line.strip():
            continue
        is_heading = bool(_HEADING.match(line) or _bare_heading(line))
        if section is not None and not is_heading and looks_like_boilerplate(line):
            skipped_boilerplate += 1
            continue
        if looks_like_instruction(line):
            result.ignored_lines.append(line.strip()[:MAX_REQUIREMENT_CHARS])
            continue
        heading = _HEADING.match(line)
        bullet = _BULLET.match(line)
        title = next(g for g in heading.groups() if g) if heading and not bullet else None
        title = title or (None if bullet else _bare_heading(line))
        if title:
            section = _section_kind(title)
            saw_section = saw_section or section is not None
            continue
        if not bullet:
            if section is not None:
                for item in _plain_items(line):
                    _add(result, item, section)
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

    if skipped_boilerplate:
        result.warnings.append(f"{skipped_boilerplate} line(s) about pay, benefits or hiring policy were left out.")
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

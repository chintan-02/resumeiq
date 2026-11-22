"""Resume-wide checks, as a pass/warn checklist. There is deliberately no overall score.

Ported from v0.9 (resume_structure_advisor, sentence_quality, resume_parser
template detection). Each check says what it found and why it matters; none of
them claims to predict what an ATS or a recruiter will do.
"""

from __future__ import annotations

import re

from .models import HealthCheck, SourceDocument
from .tailor import has_result

_BULLET = re.compile(r"^\s*[-*•]\s+(.*\S)")
_HEADING_MD = re.compile(r"^\s*#{1,6}\s*(.+?)\s*$")
_HEADING_PLAIN = re.compile(r"^\s*([A-Za-z][A-Za-z &/]{2,40}?)\s*:?\s*$")

SECTION_ALIASES = {
    "experience": ["experience", "work experience", "professional experience", "employment", "employment history"],
    "education": ["education", "academic background"],
    "skills": ["skills", "technical skills", "core skills", "tools"],
    "projects": ["projects", "project experience", "selected projects"],
}
WEAK_OPENINGS = [
    "responsible for",
    "worked on",
    "helped with",
    "helped",
    "assisted with",
    "assisted",
    "participated in",
    "involved in",
    "contributed to",
    "handled",
]
GENERIC_PHRASES = [
    "results-driven",
    "results driven",
    "detail-oriented",
    "detail oriented",
    "team player",
    "hardworking",
    "hard-working",
    "self-motivated",
    "fast learner",
    "quick learner",
    "passionate professional",
    "dynamic professional",
    "proven track record",
    "excellent communication skills",
    "problem-solving skills",
    "go-getter",
    "think outside the box",
    "synergy",
    # vague phrases
    "leveraging data-driven insights",
    "optimize business outcomes",
    "drive business growth",
    "strategic initiatives",
    "value-added solutions",
    "actionable insights",
]
TEMPLATE_PLACEHOLDERS = [
    "your name",
    "professional title",
    "company name",
    "year to year",
    "month, year",
    "email address",
    "phone number",
    "linkedin url",
    "github/portfolio url",
    "result oriented statement",
    "university name",
    "institution name",
    "graduation year",
    "lorem ipsum",
    "[add measurable result]",
    "[your verb]",
    "[action verb]",
]


def _sections(text: str) -> set[str]:
    found = set()
    for line in text.splitlines():
        match = _HEADING_MD.match(line) or (_HEADING_PLAIN.match(line) if len(line.split()) <= 4 else None)
        if not match:
            continue
        name = match.group(1).strip().strip("*").lower()
        for key, aliases in SECTION_ALIASES.items():
            if any(name == a or name.startswith(a + " ") for a in aliases):
                found.add(key)
    return found


def check_resume(document: SourceDocument) -> list[HealthCheck]:
    text = document.text
    lower = text.lower()
    bullets = [m.group(1) for line in text.splitlines() if (m := _BULLET.match(line))]
    words = len(text.split())
    checks: list[HealthCheck] = []

    has_contact = (
        "[email hidden]" in text or "[phone hidden]" in text or bool(re.search(r"@|\+?\d[\d\s().-]{7,}\d", text))
    )
    checks.append(
        HealthCheck(
            id="contact",
            label="Contact details",
            status="pass" if has_contact else "warn",
            detail="An email or phone number is present (hidden here for privacy)."
            if has_contact
            else "No email or phone number was found. Recruiters need a way to reach you.",
        )
    )

    sections = _sections(text)
    missing = []
    if "experience" not in sections and "projects" not in sections:
        missing.append("Experience or Projects")
    if "education" not in sections:
        missing.append("Education")
    if "skills" not in sections:
        missing.append("Skills")
    checks.append(
        HealthCheck(
            id="sections",
            label="Standard sections",
            status="warn" if missing else "pass",
            detail=(
                "Missing or unlabelled: "
                + ", ".join(missing)
                + ". Clear headings help readers and parsers find things."
                if missing
                else "Experience, Education and Skills sections were found."
            ),
            items=missing,
        )
    )

    if words < 200:
        length = ("warn", f"About {words} words. That is short; most resumes need room for 3 to 5 bullets per role.")
    elif words > 1100:
        length = ("warn", f"About {words} words, likely more than two pages. Cut older or less relevant bullets.")
    else:
        length = ("pass", f"About {words} words, a typical one-to-two-page length.")
    checks.append(HealthCheck(id="length", label="Length", status=length[0], detail=length[1]))

    if bullets:
        with_results = sum(has_result(b) for b in bullets)
        enough = with_results * 3 >= len(bullets)
        checks.append(
            HealthCheck(
                id="results",
                label="Measurable results",
                status="pass" if enough else "warn",
                detail=f"{with_results} of {len(bullets)} bullets show a measured result (a %, $, x, or before and after). "
                + ("" if enough else "Aim for at least one in three, using only numbers you can stand behind."),
            )
        )
        weak = [b for b in bullets if any(b.lower().startswith(w) for w in WEAK_OPENINGS)]
        checks.append(
            HealthCheck(
                id="weak_openings",
                label="Bullet openings",
                status="warn" if weak else "pass",
                detail=(
                    f"{len(weak)} bullet(s) open by describing a role rather than an action. Start with what you did, "
                    "but keep the claim true: if you contributed, say what your part was."
                    if weak
                    else "Bullets open with an action."
                ),
                items=weak,
            )
        )
        first_person = [b for b in bullets if re.search(r"(^|\s)(I|my|me)\s", b)]
        checks.append(
            HealthCheck(
                id="first_person",
                label="First person",
                status="warn" if first_person else "pass",
                detail="Resume bullets usually leave out “I” and “my”."
                if first_person
                else "Bullets are written without “I” or “my”.",
                items=first_person,
            )
        )
    else:
        checks.append(
            HealthCheck(
                id="bullets",
                label="Bullets",
                status="warn",
                detail="No bullet points were found. Bullets make experience easier to scan and to match.",
            )
        )

    generic = sorted({p for p in GENERIC_PHRASES if p in lower})
    checks.append(
        HealthCheck(
            id="generic",
            label="Generic phrases",
            status="warn" if generic else "pass",
            detail="These phrases appear on many resumes and prove nothing on their own. Replace them with a specific example."
            if generic
            else "No stock phrases such as “results-driven” or “team player”.",
            items=generic,
        )
    )

    placeholders = sorted({p for p in TEMPLATE_PLACEHOLDERS if p in lower})
    checks.append(
        HealthCheck(
            id="placeholders",
            label="Template or placeholder text",
            status="warn" if placeholders else "pass",
            detail="Fill or remove these before you send the resume." if placeholders else "No template text left in.",
            items=placeholders,
        )
    )

    has_dates = bool(re.search(r"\b(19|20)\d{2}\b", text))
    checks.append(
        HealthCheck(
            id="dates",
            label="Dates",
            status="pass" if has_dates else "warn",
            detail="Roles and education show years."
            if has_dates
            else "No years were found. Add dates to roles and education.",
        )
    )
    return checks

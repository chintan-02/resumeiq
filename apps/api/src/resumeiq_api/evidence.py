"""Split source documents into evidence items with exact character offsets.

Simple meaning: cut a resume into sentences and bullets, and remember exactly
where each one sits in the original text.
Technical meaning: line-and-sentence segmentation that preserves offsets, so for
every item `document.text[item.start:item.end] == item.text` always holds. That
invariant is what makes a citation trustworthy.
"""

from __future__ import annotations

import re

from .levels import evidence_level
from .models import EvidenceItem, SourceDocument

_BULLET = re.compile(r"^(\s*(?:[-*•]|\d+[.)])\s+)")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")
MIN_WORDS = 4


def _is_heading(line: str) -> bool:
    stripped = line.strip()
    if stripped.startswith("#"):
        return True
    if stripped.startswith("**") and stripped.endswith("**") and stripped.count("**") == 2:
        return True
    if stripped.endswith(":") and len(stripped.split()) <= 6:
        return True
    # Short lines with no sentence punctuation and a separator are contact or
    # meta lines ("Edmonton, AB · name@example.com").
    return "·" in stripped and not stripped.endswith(".")


def _spans_in_line(line: str, line_start: int) -> list[tuple[int, int]]:
    """Return (start, end) offsets of the sentences inside one line."""
    marker = _BULLET.match(line)
    offset = marker.end() if marker else len(line) - len(line.lstrip())
    body = line[offset:].rstrip()
    spans: list[tuple[int, int]] = []
    cursor = 0
    for match in _SENTENCE_END.finditer(body):
        spans.append((cursor, match.start()))
        cursor = match.end()
    spans.append((cursor, len(body)))
    return [(line_start + offset + s, line_start + offset + e) for s, e in spans if e > s]


def segment(document: SourceDocument) -> list[EvidenceItem]:
    items: list[EvidenceItem] = []
    position = 0
    for line in document.text.splitlines(keepends=True):
        line_start = position
        position += len(line)
        content = line.rstrip("\r\n")
        if not content.strip() or _is_heading(content):
            continue
        # Skill lists ("Skills: Python, SQL") are bare mentions; keep them, the
        # level rules will rate them as awareness only.
        for start, end in _spans_in_line(content, line_start):
            text = document.text[start:end]
            if len(text.split()) < MIN_WORDS:
                continue
            items.append(
                EvidenceItem(
                    id=f"{document.id}-E{len(items) + 1:02d}",
                    document_id=document.id,
                    start=start,
                    end=end,
                    text=text,
                    level=evidence_level(text),
                )
            )
    return items

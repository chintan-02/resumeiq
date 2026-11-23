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
MAX_REWRITE_EVIDENCE_CHARS = 400


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


_RESUME_BULLET = re.compile(r"^(\s*[-*•●▪◦]\s+)")
_RESUME_TITLE = re.compile(r"^[^|\n]+\|\s*(?:\[link hidden\]|https?://|github\.com|GitHub\b)", re.I)


def _blocks(text: str):
    """Yield line offsets and keep explicitly indented bullet continuations together."""
    offset = 0
    pending = ""
    start = 0
    for line in text.splitlines(keepends=True):
        continuation = line[:1] in (" ", "\t") and line.strip() and not _RESUME_BULLET.match(line)
        if pending and not continuation:
            yield start, pending
            pending = ""
        if pending:
            pending += line
        elif _RESUME_BULLET.match(line):
            start, pending = offset, line
        else:
            yield offset, line
        offset += len(line)
    if pending:
        yield start, pending


def _line_offsets(text: str):
    offset = 0
    for line in text.splitlines(keepends=True):
        yield offset, line
        offset += len(line)


def segment(document: SourceDocument, *, preserve_bullets: bool = False) -> list[EvidenceItem]:
    items: list[EvidenceItem] = []
    blocks = _blocks(document.text) if preserve_bullets else _line_offsets(document.text)
    for line_start, line in blocks:
        content = line.rstrip("\r\n")
        bullet = _RESUME_BULLET.match(content) if preserve_bullets else None
        if not bullet and (not content.strip() or _is_heading(content)):
            continue
        if preserve_bullets and not bullet and (_RESUME_TITLE.match(content) or content.strip().isupper()):
            continue
        # Skill lists ("Skills: Python, SQL") are bare mentions; keep them, the
        # level rules will rate them as awareness only.
        if bullet and len(content.rstrip()) - bullet.end() <= MAX_REWRITE_EVIDENCE_CHARS:
            spans = [(line_start + bullet.end(), line_start + len(content.rstrip()))]
        else:
            spans = [
                span for offset, part in _line_offsets(content) for span in _spans_in_line(part, line_start + offset)
            ]
        for start, end in spans:
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

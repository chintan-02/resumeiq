"""Mask contact details before text is matched, shown or sent to a model.

Ported from the v0.9 privacy_tools module. Masking is deliberately broad: a
false positive hides a harmless string, a false negative leaks contact data.
"""

from __future__ import annotations

import re

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_URL = re.compile(r"\b(?:https?://|www\.)\S+|\b(?:linkedin\.com|github\.com)/\S+", re.I)
_PHONE = re.compile(r"(?<![\w.])\+?\d[\d\s().-]{7,}\d(?![\w.])")


def mask_pii(text: str) -> str:
    text = _EMAIL.sub("[email hidden]", text)
    text = _URL.sub("[link hidden]", text)
    return _PHONE.sub("[phone hidden]", text)

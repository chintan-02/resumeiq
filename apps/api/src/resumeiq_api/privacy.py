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


# Privacy mode (ported from v0.9 privacy_tools, generalised beyond a fixed city list).
_REGIONS = (
    "AB|BC|MB|NB|NL|NS|NT|NU|ON|PE|QC|SK|YT|Alberta|British Columbia|Manitoba|New Brunswick|Newfoundland and Labrador|"
    "Nova Scotia|Ontario|Prince Edward Island|Quebec|Saskatchewan|Yukon|"
    "AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|"
    "OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY|DC|Canada|USA|United States|India|UK|United Kingdom"
)
_LOCATION = re.compile(rf"\b[A-Z][a-zA-Z.'-]+(?:\s[A-Z][a-zA-Z.'-]+)?,\s?(?:{_REGIONS})\b")
_HEADING_WORDS = {
    "summary",
    "experience",
    "education",
    "skills",
    "projects",
    "profile",
    "certifications",
    "contact",
    "objective",
    "resume",
}


def mask_location(text: str) -> str:
    return _LOCATION.sub("[location hidden]", text)


def mask_header_name(text: str) -> str:
    """Mask the name on the first line when it looks like one: 2-4 capitalised words, no digits."""
    lines = text.split("\n")
    for i, line in enumerate(lines):
        stripped = line.strip().lstrip("#").strip()
        if not stripped:
            continue
        name = re.match(r"^((?:[A-Z][a-zA-Z'-]+\s+){1,3}[A-Z][a-zA-Z'-]+)\b", stripped)
        if name and not re.search(r"\d|@", name.group(1)) and not set(name.group(1).lower().split()) & _HEADING_WORDS:
            lines[i] = line.replace(name.group(1), "[name hidden]", 1)
        break
    return "\n".join(lines)


def privacy_mode(text: str) -> str:
    """Everything mask_pii hides, plus the header name and city/region pairs."""
    return mask_location(mask_header_name(mask_pii(text)))


def mask_line(text: str) -> str:
    """For a single cited line (drafting prompts): contact details and locations, but no name masking.

    Name masking looks at a document's first line; applied to one bullet, it would hide its
    opening words ("Deployed Azure Container Apps…") as if they were a name.
    """
    return mask_location(mask_pii(text))

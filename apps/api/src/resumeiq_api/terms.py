"""Text normalisation shared by the keyword matchers.

Simple meaning: turn a sentence into a small set of comparable words.
Technical meaning: lowercase, map known synonyms to one canonical token, tokenize,
apply a light suffix stemmer and drop stop words and generic requirement words.
"""

from __future__ import annotations

import re

# Phrase-level synonyms, applied before tokenizing. Keep this list short and
# factual: semantic similarity is the embedding matcher's job, not this one's.
_SYNONYMS: list[tuple[str, str]] = [
    (r"\bgoogle cloud storage\b", "gcs"),
    (r"\bgoogle cloud platform\b|\bgoogle cloud\b", "gcp"),
    (r"\bamazon web services\b", "aws"),
    (r"\bk8s\b", "kubernetes"),
    (r"\bpostgres\b", "postgresql"),
    (r"\bpyspark\b", "spark"),
    (r"\bsklearn\b|\bscikit learn\b", "scikit-learn"),
    (r"\ba/b\b", "ab"),
    (r"\bci/cd\b", "cicd"),
    (r"\bpower bi\b", "powerbi"),
    (r"\bml\b", "machine learning"),
    (r"\bdockerfiles?\b", "docker dockerfile"),
    (r"\bdocker-compose\b", "docker compose"),
    (r"\bfastapi\b", "fastapi api"),
    (r"\bflask\b", "flask api"),
]

_STOP = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "with",
    "for",
    "to",
    "of",
    "in",
    "on",
    "at",
    "by",
    "as",
    "such",
    "like",
    "another",
    "other",
    "into",
    "from",
    "that",
    "this",
    "their",
    "our",
    "your",
    "my",
    "i",
    "we",
    "you",
    "it",
    "its",
    "is",
    "are",
    "be",
    "each",
    "every",
    "both",
    "all",
    "per",
    "via",
    "than",
    "then",
    "before",
    "after",
    "when",
    "while",
    "using",
    "use",
    "used",
}

# Words that describe how much or how well, not what. They carry no evidence.
_GENERIC = {
    "experience",
    "experienced",
    "hands-on",
    "hands",
    "years",
    "year",
    "strong",
    "solid",
    "ability",
    "able",
    "knowledge",
    "understanding",
    "familiarity",
    "familiar",
    "proficiency",
    "proficient",
    "skill",
    "skills",
    "good",
    "excellent",
    "proven",
    "demonstrated",
    "plus",
    "tool",
    "tools",
    "platform",
    "platforms",
    "similar",
    "relevant",
    "related",
}

_TOKEN = re.compile(r"[a-z0-9][a-z0-9+#.\-]*")
# No "er" suffix: it would turn tool names like "docker" into "dock".
_SUFFIXES = ("ments", "ment", "ings", "ing", "ies", "ed", "es")


def _stem(token: str) -> str:
    """Light, consistent stemmer. Both sides of a comparison are stemmed the same way."""
    if any(ch.isdigit() for ch in token) or "-" in token or "+" in token or "#" in token:
        return token
    for suffix in _SUFFIXES:
        if token.endswith(suffix) and len(token) - len(suffix) >= 4:
            stem = token[: -len(suffix)]
            return stem + "y" if suffix == "ies" else stem
    if token.endswith("s") and not token.endswith("ss") and len(token) >= 4:
        return token[:-1]
    return token


def normalize(text: str) -> str:
    out = text.lower()
    for pattern, replacement in _SYNONYMS:
        out = re.sub(pattern, replacement, out)
    return out


def tokens(text: str) -> list[str]:
    raw = _TOKEN.findall(normalize(text))
    return [_stem(t.strip(".-")) for t in raw if t.strip(".-")]


def content_terms(text: str) -> set[str]:
    """Words that carry meaning: no stop words, no generic qualifiers."""
    return {t for t in tokens(text) if t not in _STOP and t not in _GENERIC and len(t) > 1}


# Action verbs are judged by the level rules in levels.py, so the rule-aware
# matcher leaves them out of the topic overlap.
_ACTION_STEMS = {
    _stem(w)
    for w in (
        "build built design designed develop developed implement implemented deploy deployed "
        "deployment write wrote written automate automated lead led own owned owns manage "
        "managed set up create created maintain maintained work worked clean cleaned analyze "
        "analyzed communicate communicated explain explained track tracked report reported "
        "drive architect mentor responsible"
    ).split()
}


def topic_terms(text: str) -> set[str]:
    """Content terms minus action verbs: what the requirement is about."""
    return {t for t in content_terms(text) if t not in _ACTION_STEMS}


_ALTERNATIVE = re.compile(r"([\w+#.\-/]+)((?:,\s*[\w+#.\-/]+)*)(?:,)?\s+or\s+(?:another\s+)?([\w+#.\-/]+)", re.I)


def term_units(text: str, terms: set[str]) -> list[frozenset[str]]:
    """Group alternatives so either one satisfies the requirement.

    "such as GCP or AWS" -> one unit {gcp, aws}; every other term is its own unit.
    """
    units: list[frozenset[str]] = []
    grouped: set[str] = set()
    for match in _ALTERNATIVE.finditer(normalize(text)):
        words = [match.group(1), *re.findall(r"[\w+#.\-/]+", match.group(2) or ""), match.group(3)]
        group = frozenset(t for w in words for t in tokens(w) if t in terms)
        if len(group) >= 2:
            units.append(group)
            grouped |= group
    units += [frozenset({t}) for t in sorted(terms - grouped)]
    return units

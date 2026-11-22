"""Matcher v2: the keyword-rules matcher with a better reading of the requirement.

v1 treated every word of a requirement as something the evidence must show, so a
compound requirement ("Strong fundamentals in Python and TypeScript, with CRUD
applications using frameworks such as React") was judged on ten words at once.
v2 changes only how the requirement is read; retrieval, citations and the
strength rules are the same as v1.

1. Alternatives: "FastAPI/Flask", "(GCP, AWS, or Azure)" and "such as X or Y" are
   one component that any listed option satisfies (labelling guide, Step 1). The
   noun the examples illustrate ("relational databases such as PostgreSQL") joins
   that component.
2. Descriptor words that say how good or what kind, not what ("fundamentals",
   "frameworks", "major", "technical"), are not components.
3. A short list of concept groups lets common paraphrases count: a requirement
   that says "stakeholders" is met by evidence about "managers" or "clients".

Thresholds are tuned on eval_v0 (dev and test together, since v0's test split was
viewed while v2 was designed). eval_v1 is the held-out test set.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from .levels import LEVEL_WORDS
from .matching import KeywordMatcher, Thresholds, apply_strength_rules
from .models import Coverage, EvidenceItem, Level, Requirement, RequirementResult
from .terms import term_units, tokens, topic_terms

# Slashes that are part of one name, not "either/or".
_ONE_NAME_SLASH = re.compile(r"\b(ci/cd|a/b|i/o|tcp/ip|ui/ux|b2b/b2c)\b", re.I)
_SLASH_OR = re.compile(r"(?<=[\w+#])\s*/\s*(?=[\w])")
_PAREN_LIST = re.compile(r"\(([^()]*\bor\b[^()]*)\)")
_RAW_ALTERNATIVE = re.compile(r"([\w+#.\-]+)((?:,\s*[\w+#.\-]+)*)(?:,)?\s+or\s+([\w+#.\-]+)", re.I)
_EXAMPLES = re.compile(
    r"((?:[\w+#.\-]+\s+){0,2}[\w+#.\-]+)\s+(?:such as|like|e\.g\.,?|for example|including)\s+([^.;]+)",
    re.I,
)

_DESCRIPTORS = {
    content
    for word in (
        "fundamentals fundamental framework frameworks major technical modern production-grade "
        "application applications service services system systems method methods project projects "
        "against solution solutions environment environments team teams production workload workloads"
    ).split()
    for content in tokens(word)
}

# Small, general concept groups. A requirement term in a group is also met by any
# other member. Kept short on purpose: broad similarity is the embedding matcher's job.
_CONCEPTS = [
    "stakeholder stakeholders manager managers executive executives leadership director client clients customer customers business audience audiences staff",
    "non-technical plain layperson",
    "cloud gcp aws azure vertex sagemaker bigquery dataproc",
    "api apis endpoint endpoints",
    "dashboard dashboards report reports",
    "machine learning ml model models",
    "dataset datasets data table tables",
    "recurring daily weekly nightly monthly scheduled cron",
    "pipeline pipelines job jobs dag dags workflow workflows script scripts etl",
    "ci cicd workflow workflows actions jenkins gitlab",
]
# Compound terms that must match as a whole, not word by word.
_COMPOUNDS = [(re.compile(r"\bfeature stores?\b", re.I), "featurestore")]
_GROUPS = [frozenset(t for w in group.split() for t in tokens(w)) for group in _CONCEPTS]


def read_requirement(text: str) -> tuple[str, list[frozenset[str]]]:
    """Normalised requirement text and its components (each a set of acceptable terms)."""
    protected = {}

    def protect(match: re.Match[str]) -> str:
        key = f"zz{len(protected)}zz"
        protected[key] = match.group(0)
        return key

    norm = _ONE_NAME_SLASH.sub(protect, text)
    norm = _SLASH_OR.sub(" or ", norm)
    norm = _PAREN_LIST.sub(lambda m: f" such as {m.group(1)}", norm)
    for pattern, token in _COMPOUNDS:
        norm = pattern.sub(token, norm)
    for key, value in protected.items():
        norm = norm.replace(key, value)

    wanted = topic_terms(norm) - _DESCRIPTORS
    units = term_units(norm, wanted)

    # term_units reads alternatives after synonyms are applied, so "FastAPI or Flask"
    # becomes "fastapi api or flask api" and only "api or flask" is grouped. Group the
    # words as written instead: every token of every listed option joins one component.
    for match in _RAW_ALTERNATIVE.finditer(norm):
        words = [match.group(1), *re.findall(r"[\w+#.\-]+", match.group(2) or ""), match.group(3)]
        group = {t for w in words for t in tokens(w) if t in wanted}
        if len(group) >= 2:
            merged = frozenset().union(*(u for u in units if u & group))
            units = [u for u in units if not u & group] + [merged]

    # "relational databases such as PostgreSQL": head noun and examples form one component.
    for match in _EXAMPLES.finditer(norm):
        # Only the noun the examples illustrate joins them ("databases" in "relational
        # databases such as PostgreSQL"); a descriptor ("tools", "frameworks") does not.
        head = {t for t in tokens(match.group(1).split()[-1]) if t in wanted}
        examples = {t for t in tokens(re.split(r"\s+and\s+", match.group(2))[0]) if t in wanted}
        together = head | examples
        if len(together) < 2:
            continue
        merged = frozenset().union(*(u for u in units if u & together))
        units = [u for u in units if not u & together] + [merged]

    expanded: list[frozenset[str]] = []
    for unit in units:
        extra = frozenset().union(*(g for g in _GROUPS if g & unit))
        if unit | extra not in expanded:  # "machine learning" is one component, not two
            expanded.append(unit | extra)
    return norm, expanded


class KeywordMatcherV2(KeywordMatcher):
    def __init__(self, thresholds: Thresholds) -> None:
        super().__init__(thresholds, use_rules=True)
        self.name = "keyword-rules-v2"

    def match(self, requirement: Requirement, evidence: Sequence[EvidenceItem]) -> RequirementResult:
        _, units = read_requirement(requirement.text)
        return self._match_units(requirement, evidence, units)


_NAMED = re.compile(r"(?<!^)(?<![.!?]\s)\b([A-Z][\w+#.\-]*)")


def named_terms(requirement_text: str) -> set[str]:
    """Words the posting capitalises after the first word: tool and skill names (Airflow, SQL, Docker)."""
    named = set()
    for word in _NAMED.findall(requirement_text.strip()):
        parts = tokens(word)
        if len(parts) == 1 and len(parts[0]) > 1:  # skip expanded acronyms (ML) and fragments (A/B)
            named.update(parts)
    return named


def per_component_strength(item_units: dict[str, set[frozenset[str]]]):
    """Strength judged per named component (labelling guide: every component at the required level).

    For each named tool or skill in the requirement, take the best level among the cited lines
    that mention it; the requirement is shown at the weakest of those. So "Skills: Looker" plus
    "Built weekly sales reports in Excel" no longer reads as building Looker dashboards: Looker
    itself is only listed. Generic words (data, model, test) keep v2's strongest-line rule,
    because a weak line that happens to say "data" says nothing about the skill.
    """

    def rule(status: Coverage, requirement: Requirement, cited: Sequence[EvidenceItem]) -> tuple[Coverage, str | None]:
        status, reason = apply_strength_rules(status, requirement, cited)
        if status is Coverage.NOT_FOUND or not cited:
            return status, reason
        named = named_terms(requirement.text)
        needed = requirement.required_level
        levels: dict[frozenset[str], tuple[Level, str]] = {}
        for item in cited:
            for unit in item_units.get(item.id, set()):
                if unit & named and (unit not in levels or item.level > levels[unit][0]):
                    levels[unit] = (item.level, item.id)
        if not levels:
            return status, reason
        weakest_unit = min(levels, key=lambda u: (levels[u][0], sorted(u)))
        weakest, weakest_id = levels[weakest_unit]
        if weakest >= needed:
            return status, reason
        name = " or ".join(sorted(weakest_unit & named))
        if weakest >= Level.USED or needed <= Level.USED and weakest >= Level.AWARE and status is Coverage.PARTIAL:
            return Coverage.PARTIAL, (
                f"'{name}' is only shown at {LEVEL_WORDS[weakest]} ({weakest_id}); "
                f"this requirement asks for {LEVEL_WORDS[needed]} of every named skill."
            )
        if needed >= Level.USED:
            return Coverage.NOT_FOUND, (
                f"'{name}' is only shown at {LEVEL_WORDS[weakest]} ({weakest_id}), not used in any line; "
                f"this requirement asks for {LEVEL_WORDS[needed]}."
            )
        return status, reason

    return rule


class KeywordMatcherV3(KeywordMatcherV2):
    """v2's requirement reading, with strength judged per component instead of per strongest line."""

    def __init__(self, thresholds: Thresholds) -> None:
        super().__init__(thresholds)
        self.name = "keyword-rules-v3"

    def _strength_rule(self, item_units):
        return per_component_strength(item_units)

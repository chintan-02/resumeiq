"""Conservative checks for requirements that keyword overlap cannot establish."""

from __future__ import annotations

import re
from collections.abc import Sequence

from .matching import Thresholds
from .matching_v2 import KeywordMatcherV3, normalize_strict_phrases, per_component_strength, read_requirement
from .models import Coverage, EvidenceItem, Requirement, RequirementResult
from .terms import content_terms

_DURATION = re.compile(r"\b\d+\s*(?:\+|–\s*\d+|-\s*\d+)?\s*(?:years?|months?|yrs?)\b", re.I)
# These phrases distinguish particular tools and activities from adjacent experience.
_GATES = {
    "Langfuse": r"\blangfuse\b",
    "LangGraph": r"\blanggraph\b",
    "LangChain": r"\blangchain\b",
    "MCP": r"\b(?:mcp|model context protocol)\b",
    "Vertex AI": r"\bvertex ai\b",
    "BigQuery": r"\bbigquery\b",
    "mentoring": r"\bmentor\w*\b",
    "unit testing": r"\bunit tests?\b",
    "integration testing": r"\bintegration tests?\b",
    "enterprise data": r"\benterprise data\b",
}
_ALTERNATIVES = re.compile(r"\bor\b|\bsuch as\b|\be\.g\.", re.I)
_OBSERVABILITY = re.compile(r"\b(?:langsmith|arize phoenix|helicone|opik)\b", re.I)
_FRAMEWORK = re.compile(r"\b(?:google adk|crewai|semantic kernel|llamaindex)\b", re.I)


def _missing_evidence(requirement: Requirement, evidence: Sequence[EvidenceItem]) -> list[str]:
    text = requirement.text
    requested = [label for label, pattern in _GATES.items() if re.search(pattern, text, re.I)]
    qualified = "\n".join(
        item.text
        for item in evidence
        if item.level >= requirement.required_level
        and not re.search(r"\b(?:planned|no experience|never used|not yet|without)\b", item.text, re.I)
    )
    missing = [label for label in requested if not re.search(_GATES[label], qualified, re.I)]
    if re.search(r"\bproduction\b", text, re.I) and re.search(r"\b(?:monitor|troubleshoot)\w*\b", text, re.I):
        if not any(
            re.search(r"\bproduction\b", item.text, re.I)
            and re.search(r"\b(?:monitor|troubleshoot)\w*\b", item.text, re.I)
            and not re.search(r"\b(?:not|never|unapproved|staging)\b", item.text, re.I)
            for item in evidence
        ):
            missing.append("production monitoring or troubleshooting")

    framework_names = {"LangGraph", "LangChain"} & set(requested)
    if framework_names and re.search(r"\bor\b", text, re.I):
        has_alternative = any(label not in missing for label in framework_names)
        if re.search(r"\bsimilar\b", text, re.I) and _FRAMEWORK.search(qualified):
            has_alternative = True
        if has_alternative:
            missing = [label for label in missing if label not in framework_names]

    if "Langfuse" in missing and re.search(r"\bor another\b", text, re.I) and _OBSERVABILITY.search(qualified):
        missing.remove("Langfuse")

    if _ALTERNATIVES.search(text) and {"Vertex AI", "BigQuery"} <= set(requested):
        if any(label not in missing for label in ("Vertex AI", "BigQuery")):
            missing = [label for label in missing if label not in {"Vertex AI", "BigQuery"}]
    if re.search(r"^\s*(?:remain|stay) current\b", text, re.I) and not re.search(
        r"\b(?:kept up|stay(?:ed)? current|track(?:ed)? developments|experiment(?:ed)? with new)\b", qualified, re.I
    ):
        missing.append("how you keep up with developments in the field")
    if re.search(r"^\s*collaborat", text, re.I) and not re.search(
        r"\b(?:collaborat\w*|partnered with|worked (?:with|alongside)|coordinated with)\b", qualified, re.I
    ):
        missing.append("collaboration with the teams named in the posting")
    return missing


class KeywordMatcherV4(KeywordMatcherV3):
    """Keep the overlap score, but require direct evidence for specific constraints."""

    name = "keyword-rules-v4"

    def __init__(self, thresholds: Thresholds) -> None:
        super().__init__(thresholds)
        self.name = type(self).name

    def _strength_rule(self, item_units):
        return per_component_strength(item_units, keep_related=True)

    def _evidence_terms(self, text: str) -> set[str]:
        return content_terms(normalize_strict_phrases(text))

    def match(self, requirement: Requirement, evidence: Sequence[EvidenceItem]) -> RequirementResult:
        _, units = read_requirement(requirement.text, strict=True)
        result = self._match_units(requirement, evidence, units)
        by_id = {item.id: item for item in evidence}
        cited = [by_id[citation.evidence_id] for citation in result.citations]
        missing = _missing_evidence(requirement, cited)
        duration = _DURATION.search(requirement.text)
        checks = []
        if missing:
            checks.append(f"Direct evidence still needed for {', '.join(missing)}.")
        if duration:
            checks.append(f"Verify the {duration.group()} requirement against dated work in this area.")
        if not checks:
            return result
        # Preserve genuine related evidence while preventing a full match.
        if result.status is Coverage.SUPPORTED:
            result.status = Coverage.PARTIAL
        result.verification_notes = checks
        return result

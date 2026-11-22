"""Matchers that decide whether evidence supports a requirement.

Three families, so the evaluation can separate retrieval from judgment:

* ``keyword``: counts shared words only. The naive baseline.
* ``keyword-rules``: the same retrieval, plus the strength rules from the
  labelling guide (contributed < built < led).
* ``embedding`` / ``embedding-rules``: dense retrieval with a sentence-embedding
  model, without and with the same strength rules. Needs the optional
  ``embeddings`` extra and a model download, so it runs on a developer machine.

Thresholds are tuned on the dev split only (see resumeiq_api.evaluation).
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Protocol

from .levels import LEVEL_WORDS
from .models import Citation, Coverage, EvidenceItem, Level, Requirement, RequirementResult
from .terms import content_terms, term_units, topic_terms

MAX_CITATIONS = 3


@dataclass(frozen=True)
class Thresholds:
    """Score cut-offs. ``low`` separates not_found from partial, ``high`` partial from supported."""

    low: float
    high: float


class Matcher(Protocol):
    name: str
    thresholds: Thresholds

    def match(self, requirement: Requirement, evidence: Sequence[EvidenceItem]) -> RequirementResult: ...


def _cite(item: EvidenceItem, score: float) -> Citation:
    return Citation(
        evidence_id=item.id,
        document_id=item.document_id,
        start=item.start,
        end=item.end,
        quote=item.text,
        level=item.level,
        score=round(score, 4),
    )


def apply_strength_rules(
    status: Coverage, requirement: Requirement, cited: Sequence[EvidenceItem]
) -> tuple[Coverage, str | None]:
    """Downgrade a topic match when the evidence shows a weaker claim (guide, Step 4).

    Uses the strongest level among the cited items. Chosen on the dev split over
    "level of the first citation" (dev macro-F1 0.77 vs 0.73); see the eval report.
    """
    if status is Coverage.NOT_FOUND or not cited:
        return status, None
    strongest = max(cited, key=lambda item: item.level)
    best = strongest.level
    needed = requirement.required_level
    if best >= needed:
        return status, None
    if best <= Level.AWARE and needed >= Level.USED:
        return Coverage.NOT_FOUND, (
            f"The strongest matching evidence ({strongest.id}) only shows {LEVEL_WORDS[best]}; "
            f"this requirement asks for {LEVEL_WORDS[needed]}."
        )
    return Coverage.PARTIAL, (
        f"The strongest matching evidence ({strongest.id}) shows {LEVEL_WORDS[best]}; "
        f"this requirement asks for {LEVEL_WORDS[needed]}."
    )


def _finish(
    requirement: Requirement,
    status: Coverage,
    cited: list[tuple[EvidenceItem, float]],
    ranked_ids: list[str],
    base_reason: str,
    use_rules: bool,
) -> RequirementResult:
    reason = base_reason
    if use_rules:
        status, rule_reason = apply_strength_rules(status, requirement, [c for c, _ in cited])
        if rule_reason:
            reason = f"{base_reason} {rule_reason}"
    citations = [] if status is Coverage.NOT_FOUND else [_cite(item, s) for item, s in cited]
    return RequirementResult(
        requirement=requirement,
        status=status,
        reason=reason,
        citations=citations,
        candidates=ranked_ids,
    )


class KeywordMatcher:
    """Word-overlap matcher. ``use_rules`` turns on the strength rules."""

    def __init__(self, thresholds: Thresholds, use_rules: bool) -> None:
        self.thresholds = thresholds
        self.use_rules = use_rules
        self.name = "keyword-rules" if use_rules else "keyword"
        self._terms: Callable[[str], set[str]] = topic_terms if use_rules else content_terms

    def match(self, requirement: Requirement, evidence: Sequence[EvidenceItem]) -> RequirementResult:
        wanted = self._terms(requirement.text)
        units = term_units(requirement.text, wanted) if wanted else []  # "GCP or AWS" counts once
        return self._match_units(requirement, evidence, units)

    def _match_units(
        self, requirement: Requirement, evidence: Sequence[EvidenceItem], units: list[frozenset[str]]
    ) -> RequirementResult:
        if not units:
            return RequirementResult(
                requirement=requirement,
                status=Coverage.NOT_FOUND,
                reason="The requirement has no specific skill or topic to look for. Edit it to be more specific.",
            )
        pool_terms = {item.id: content_terms(item.text) for item in evidence}
        # Rare terms identify evidence better than common ones ("Azure" beats "model"):
        # weight each unit by inverse document frequency within this candidate's pool.
        doc_freq = {u: sum(bool(u & t) for t in pool_terms.values()) for u in units}
        weight = {u: math.log((len(evidence) + 1) / (doc_freq[u] + 1)) + 1 for u in units}
        scored = []
        for item in evidence:
            shared = {unit for unit in units if unit & pool_terms[item.id]}
            if shared:
                scored.append((item, shared))
        scored.sort(key=lambda pair: (-sum(weight[u] for u in pair[1]), -int(pair[0].level), pair[0].id))
        ranked_ids = [item.id for item, _ in scored]

        # Greedy cover: cite the items that together explain the most requirement terms.
        covered: set[frozenset[str]] = set()
        cited: list[tuple[EvidenceItem, float]] = []
        for item, shared in scored:
            if len(cited) >= MAX_CITATIONS:
                break
            if shared - covered:
                covered |= shared
                cited.append((item, len(shared) / len(units)))

        coverage = len(covered) / len(units)
        if coverage >= self.thresholds.high:
            status = Coverage.SUPPORTED
        elif coverage >= self.thresholds.low:
            status = Coverage.PARTIAL
        else:
            status = Coverage.NOT_FOUND

        def label(group: set[frozenset[str]]) -> str:
            return ", ".join(sorted(" or ".join(sorted(u)) for u in group)) or "none"

        reason = (
            f"Found {len(covered)} of {len(units)} key terms "
            f"(found: {label(covered)}; not found: {label(set(units) - covered)})."
        )
        return _finish(requirement, status, cited, ranked_ids, reason, self.use_rules)


class EmbeddingMatcher:
    """Dense retrieval with a sentence-embedding model.

    The model is loaded lazily so the API and tests do not need it installed.
    """

    def __init__(
        self,
        thresholds: Thresholds,
        use_rules: bool,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        encoder: Callable[[list[str]], list[list[float]]] | None = None,
    ) -> None:
        self.thresholds = thresholds
        self.use_rules = use_rules
        self.model_name = model_name
        self.name = "embedding-rules" if use_rules else "embedding"
        self._encoder = encoder
        self._cache: dict[str, list[float]] = {}

    def _encode(self, texts: list[str]) -> list[list[float]]:
        missing = [t for t in texts if t not in self._cache]
        if missing:
            if self._encoder is None:
                from sentence_transformers import SentenceTransformer  # optional dependency

                model = SentenceTransformer(self.model_name)
                self._encoder = lambda batch: model.encode(batch, normalize_embeddings=True).tolist()
            for text, vector in zip(missing, self._encoder(missing), strict=True):
                self._cache[text] = vector
        return [self._cache[t] for t in texts]

    @staticmethod
    def _cosine(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b, strict=True))
        norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
        return dot / norm if norm else 0.0

    def match(self, requirement: Requirement, evidence: Sequence[EvidenceItem]) -> RequirementResult:
        if not evidence:
            return RequirementResult(
                requirement=requirement, status=Coverage.NOT_FOUND, reason="No evidence to compare."
            )
        vectors = self._encode([requirement.text] + [e.text for e in evidence])
        query, rest = vectors[0], vectors[1:]
        scored = sorted(
            ((item, self._cosine(query, vec)) for item, vec in zip(evidence, rest, strict=True)),
            key=lambda pair: (-pair[1], pair[0].id),
        )
        ranked_ids = [item.id for item, _ in scored]
        best_score = scored[0][1]
        if best_score >= self.thresholds.high:
            status = Coverage.SUPPORTED
        elif best_score >= self.thresholds.low:
            status = Coverage.PARTIAL
        else:
            status = Coverage.NOT_FOUND
        cited = [(item, s) for item, s in scored[:MAX_CITATIONS] if s >= self.thresholds.low][:2]
        reason = "Closest evidence by meaning." if cited else "No evidence was close in meaning."
        return _finish(requirement, status, cited, ranked_ids, reason, self.use_rules)


DEFAULT_THRESHOLDS = {
    # Overwritten by tuned values in evals/reports; these are the pre-tuning defaults.
    "keyword": Thresholds(low=0.34, high=0.67),
    "keyword-rules": Thresholds(low=0.34, high=0.67),
    "keyword-rules-v2": Thresholds(low=0.34, high=0.67),
    "embedding": Thresholds(low=0.35, high=0.55),
    "embedding-rules": Thresholds(low=0.35, high=0.55),
}


def build_matcher(name: str, thresholds: Thresholds | None = None) -> Matcher:
    chosen = thresholds or DEFAULT_THRESHOLDS[name]
    if name in ("keyword", "keyword-rules"):
        return KeywordMatcher(chosen, use_rules=name.endswith("rules"))
    if name == "keyword-rules-v2":
        from .matching_v2 import KeywordMatcherV2  # imported here: it subclasses KeywordMatcher

        return KeywordMatcherV2(chosen)
    if name in ("embedding", "embedding-rules"):
        return EmbeddingMatcher(chosen, use_rules=name.endswith("rules"))
    raise ValueError(f"Unknown matcher: {name}")

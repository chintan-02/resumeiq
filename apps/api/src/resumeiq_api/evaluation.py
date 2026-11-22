"""Evaluate matchers on the labelled requirement → evidence set.

Two questions, measured separately so a failure can be traced:

* Retrieval: did the right evidence appear near the top? (evidence recall@k)
* Judgment: given what was found, was the status right? (macro-F1 over
  supported / partial / not_found, plus accuracy on keyword-trap cases)
* Citation precision: of the evidence the matcher cited, how much is truly gold?

Thresholds are tuned on the dev split and frozen before the test split is scored.
"""

from __future__ import annotations

import hashlib
import json
import random
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from .levels import evidence_level
from .matching import Matcher, Thresholds, build_matcher
from .models import Coverage, EvidenceItem, Level, Requirement

CLASSES = [c.value for c in Coverage]


@dataclass(frozen=True)
class Case:
    id: str
    requirement: Requirement
    evidence: tuple[EvidenceItem, ...]
    gold_status: str
    gold_evidence_ids: tuple[str, ...]
    trap: bool
    ambiguous: bool
    label_status: str


def dataset_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_cases(path: Path, split: str) -> list[Case]:
    data = json.loads(path.read_text(encoding="utf-8"))
    requirements = {
        r["id"]: Requirement(
            id=r["id"], text=r["text"], priority=r["priority"], required_level=Level(r["required_level"])
        )
        for job in data["jobs"].values()
        for r in job["requirements"]
    }
    pools: dict[str, tuple[EvidenceItem, ...]] = {}
    for cid, cand in data["candidates"].items():
        pools[cid] = tuple(
            EvidenceItem(
                id=e["id"],
                document_id=e["id"],
                start=0,
                end=len(e["text"]),
                text=e["text"],
                level=evidence_level(e["text"]),
            )
            for e in cand["evidence"]
        )
    cases = []
    for c in data["cases"]:
        if data["candidates"][c["candidate"]]["split"] != split:
            continue
        cases.append(
            Case(
                id=c["id"],
                requirement=requirements[c["requirement"]],
                evidence=pools[c["candidate"]],
                gold_status=c["gold_status"],
                gold_evidence_ids=tuple(c["gold_evidence_ids"]),
                trap=c["trap"],
                ambiguous=c["ambiguous"],
                label_status=c["label_status"],
            )
        )
    return cases


@dataclass(frozen=True)
class Prediction:
    case: Case
    status: str
    cited: tuple[str, ...]
    ranked: tuple[str, ...]


def predict(matcher: Matcher, cases: Iterable[Case]) -> list[Prediction]:
    out = []
    for case in cases:
        result = matcher.match(case.requirement, case.evidence)
        out.append(
            Prediction(
                case=case,
                status=result.status.value,
                cited=tuple(c.evidence_id for c in result.citations),
                ranked=tuple(result.candidates),
            )
        )
    return out


def _f1(p: float, r: float) -> float:
    return 2 * p * r / (p + r) if p + r else 0.0


def macro_f1(preds: Sequence[Prediction]) -> float:
    return classification_metrics(preds)["macro_f1"]


def classification_metrics(preds: Sequence[Prediction]) -> dict:
    confusion = {g: {p: 0 for p in CLASSES} for g in CLASSES}
    for pr in preds:
        confusion[pr.case.gold_status][pr.status] += 1
    per_class = {}
    for cls in CLASSES:
        tp = confusion[cls][cls]
        predicted = sum(confusion[g][cls] for g in CLASSES)
        actual = sum(confusion[cls].values())
        precision = tp / predicted if predicted else 0.0
        recall = tp / actual if actual else 0.0
        per_class[cls] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(_f1(precision, recall), 4),
            "support": actual,
        }
    correct = sum(confusion[c][c] for c in CLASSES)
    return {
        "n": len(preds),
        "accuracy": round(correct / len(preds), 4) if preds else 0.0,
        "macro_f1": round(sum(v["f1"] for v in per_class.values()) / len(CLASSES), 4),
        "per_class": per_class,
        "confusion": confusion,
    }


def evidence_recall_at_k(preds: Sequence[Prediction], k: int) -> dict:
    eligible = [p for p in preds if p.case.gold_evidence_ids]
    hits = sum(any(e in p.ranked[:k] for e in p.case.gold_evidence_ids) for p in eligible)
    return {"k": k, "hits": hits, "n": len(eligible), "recall": round(hits / len(eligible), 4) if eligible else 0.0}


def citation_precision(preds: Sequence[Prediction]) -> dict:
    cited = [(p, c) for p in preds for c in p.cited]
    good = sum(c in p.case.gold_evidence_ids for p, c in cited)
    return {"correct": good, "cited": len(cited), "precision": round(good / len(cited), 4) if cited else 0.0}


def subset_accuracy(preds: Sequence[Prediction], keep: Callable[[Case], bool]) -> dict:
    subset = [p for p in preds if keep(p.case)]
    correct = sum(p.status == p.case.gold_status for p in subset)
    return {"correct": correct, "n": len(subset), "accuracy": round(correct / len(subset), 4) if subset else 0.0}


def bootstrap_macro_f1(preds: Sequence[Prediction], resamples: int = 1000, seed: int = 0) -> dict:
    rng = random.Random(seed)
    scores = sorted(macro_f1([rng.choice(preds) for _ in preds]) for _ in range(resamples))
    return {
        "resamples": resamples,
        "seed": seed,
        "ci95_low": round(scores[int(0.025 * resamples)], 4),
        "ci95_high": round(scores[int(0.975 * resamples) - 1], 4),
    }


def full_report(preds: Sequence[Prediction]) -> dict:
    return {
        **classification_metrics(preds),
        "macro_f1_bootstrap": bootstrap_macro_f1(preds),
        "evidence_recall": [evidence_recall_at_k(preds, k) for k in (1, 3)],
        "citation_precision": citation_precision(preds),
        "trap_accuracy": subset_accuracy(preds, lambda c: c.trap),
        "unambiguous_accuracy": subset_accuracy(preds, lambda c: not c.ambiguous),
        "errors": [
            {
                "case": p.case.id,
                "requirement": p.case.requirement.text,
                "gold": p.case.gold_status,
                "predicted": p.status,
                "cited": list(p.cited),
                "gold_evidence": list(p.case.gold_evidence_ids),
                "trap": p.case.trap,
            }
            for p in preds
            if p.status != p.case.gold_status
        ],
    }


def _grid(start: float, stop: float, step: float) -> list[float]:
    count = int(round((stop - start) / step)) + 1
    return [round(start + i * step, 4) for i in range(count)]


GRIDS = {
    "keyword": (_grid(0.05, 0.6, 0.05), _grid(0.2, 1.0, 0.05)),
    "keyword-rules": (_grid(0.05, 0.6, 0.05), _grid(0.2, 1.0, 0.05)),
    "keyword-rules-v2": (_grid(0.05, 0.6, 0.05), _grid(0.2, 1.0, 0.05)),
    "keyword-rules-v3": (_grid(0.05, 0.6, 0.05), _grid(0.2, 1.0, 0.05)),
    "embedding": (_grid(0.15, 0.6, 0.025), _grid(0.3, 0.85, 0.025)),
    "embedding-rules": (_grid(0.15, 0.6, 0.025), _grid(0.3, 0.85, 0.025)),
}


def tune(name: str, dev_cases: Sequence[Case], matcher_factory=build_matcher) -> tuple[Thresholds, float]:
    """Grid-search thresholds on dev. Ties go to the first pair in (low, high) ascending order."""
    lows, highs = GRIDS[name]
    best: tuple[Thresholds, float] | None = None
    shared = matcher_factory(name)  # reuse one matcher so embeddings are encoded once
    for low in lows:
        for high in highs:
            if low >= high:
                continue
            shared.thresholds = Thresholds(low=low, high=high)
            score = macro_f1(predict(shared, dev_cases))
            if best is None or score > best[1]:
                best = (Thresholds(low=low, high=high), score)
    assert best is not None
    return best

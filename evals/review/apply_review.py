"""Apply a completed label review to the dataset and measure reviewer agreement.

Reads evals/review/review_primary.csv (required) and review_second_blind.csv (optional).

* your_status empty or equal to the draft -> label_status "reviewed".
* your_status different -> gold label replaced, label_status "adjudicated", note kept.
* If the blind sheet is filled in, writes evals/reports/review_v0.md with agreement and
  Cohen's kappa on those cases, and lists every disagreement to discuss.

Run from the repository root:  python evals/review/apply_review.py
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "evals" / "datasets" / "eval_v0.json"
REVIEW = ROOT / "evals" / "review"
REPORT = ROOT / "evals" / "reports" / "review_v0.md"
STATUSES = {"supported", "partial", "not_found"}
ALIASES = {"ok": None, "yes": None, "y": None, "": None, "not found": "not_found", "notfound": "not_found"}


def norm_status(value: str) -> str | None:
    v = value.strip().lower()
    if v in ALIASES:
        return ALIASES[v]
    v = v.replace(" ", "_")
    if v not in STATUSES:
        raise ValueError(f"Unknown status '{value}'. Use supported, partial or not_found (or leave blank to agree).")
    return v


def cohen_kappa(a: list[str], b: list[str]) -> float:
    n = len(a)
    if n == 0:
        return 0.0
    observed = sum(x == y for x, y in zip(a, b, strict=True)) / n
    ca, cb = Counter(a), Counter(b)
    expected = sum(ca[k] * cb[k] for k in set(a) | set(b)) / (n * n)
    return 1.0 if expected == 1 else (observed - expected) / (1 - expected)


def read(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def apply_primary(data: dict, rows: list[dict]) -> list[str]:
    cases = {c["id"]: c for c in data["cases"]}
    pools = {cid: {e["id"]: e["text"] for e in c["evidence"]} for cid, c in data["candidates"].items()}
    changes = []
    for row in rows:
        case = cases[row["case_id"]]
        status = norm_status(row.get("your_status", ""))
        if status is None or status == case["gold_status"]:
            case["label_status"] = "reviewed"
            continue
        ids = row.get("your_evidence_ids", "").split()
        pool = pools[case["candidate"]]
        if status != "not_found" and not ids:
            raise ValueError(f"{case['id']}: give your_evidence_ids when the status is {status}.")
        if any(i not in pool for i in ids):
            raise ValueError(f"{case['id']}: evidence ids must come from this candidate's pool: {sorted(pool)}")
        changes.append(f"{case['id']}: {case['gold_status']} -> {status}")
        case["gold_status"] = status
        case["gold_evidence_ids"] = [] if status == "not_found" else ids
        case["gold_quote"] = "" if status == "not_found" else pool[ids[0]]
        case["label_status"] = "adjudicated"
        case["rationale"] = row.get("note", "").strip() or "Changed in primary review."
        case["review_note"] = "Draft label replaced in primary review."
    return changes


def agreement_report(data: dict, blind: list[dict]) -> str:
    cases = {c["id"]: c for c in data["cases"]}
    filled = [(r["case_id"], norm_status(r["status"])) for r in blind if r.get("status", "").strip()]
    pairs = [(cid, cases[cid]["gold_status"], s) for cid, s in filled if s]
    if not pairs:
        return ""
    a, b = [p[1] for p in pairs], [p[2] for p in pairs]
    kappa = cohen_kappa(a, b)
    agree = sum(x == y for x, y in zip(a, b, strict=True))
    lines = [
        "# Label review: second reviewer agreement (eval_v0)",
        "",
        f"Blind second review of trap and ambiguous cases: {agree}/{len(pairs)} agree · Cohen's kappa {kappa:.2f}",
        "",
        "Kappa above 0.6 is usually read as substantial agreement; below 0.4 means the guide needs work.",
        "",
        "## Disagreements to discuss and settle",
        "",
        "| Case | Primary label | Second reviewer |",
        "| --- | --- | --- |",
    ]
    lines += [f"| {cid} | {x} | {y} |" for cid, x, y in pairs if x != y] or ["| none | | |"]
    return "\n".join(lines) + "\n"


def main() -> int:
    primary_path = REVIEW / "review_primary.csv"
    rows = read(primary_path)
    unreviewed = [r for r in rows if not r.get("your_status", "").strip() and not r.get("note", "").strip()]
    if len(unreviewed) == len(rows):
        print("review_primary.csv is not filled in yet; skipping the human review step.")
        return 0
    data = json.loads(DATASET.read_text(encoding="utf-8"))
    changes = apply_primary(data, rows)
    data.setdefault("changelog", []).append(
        {"version": "eval_v0 (guide 0.1)", "change": f"Primary human review applied: {len(changes)} label(s) changed."}
    )
    DATASET.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Applied review: {len(rows)} cases, {len(changes)} changed.")
    for c in changes:
        print("  " + c)

    blind_path = REVIEW / "review_second_blind.csv"
    if blind_path.exists():
        report = agreement_report(data, read(blind_path))
        if report:
            REPORT.write_text(report, encoding="utf-8")
            print(f"Wrote {REPORT.relative_to(ROOT)}")
        else:
            print("Second-reviewer sheet is still empty; skipping agreement report.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

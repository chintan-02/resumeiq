"""Held-out evaluation of the claim checker (check_claim).

Usage (from the repository root):

    python evals/run_claimcheck.py            # writes evals/reports/claimcheck_v1/
    python evals/run_claimcheck.py --check    # CI: fail if results differ from the report

History: claimcheck_v0 measured checker v0 (report kept as the historical record in
evals/reports/claimcheck_v0/). Checker v1 was designed on claimcheck_v0, which is now
development data, and scored once on claimcheck_v1, written and frozen before any v1
change. The score of checker v0 on claimcheck_v1 was recorded before the change, as
the "before" number.

What it measures:

* Block rate: of the drafts that overstate their evidence (stronger verb, new or
  changed number, new tool, wider scope, invented outcome), how many are blocked.
* False-block rate: of the honest drafts (rewording, weaker claims, placeholders,
  number formats, tool aliases), how many are wrongly blocked.

Protocol: the set was written and frozen (sha256 below) before check_claim was run
on it. The checker is not changed in response to these results; a fix needs a new
held-out set (claimcheck_v1). No model is called, so this runs in CI.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

from resumeiq_api import __version__
from resumeiq_api.rewrite import EvidenceLine, check_claim

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "evals" / "datasets" / "claimcheck_v1.json"
DEV = ROOT / "evals" / "datasets" / "claimcheck_v0.json"
OUT_DIR = ROOT / "evals" / "reports" / "claimcheck_v1"
BEFORE = OUT_DIR / "checker_v0_on_v1.json"  # recorded before checker v1 existed
FROZEN_SHA256 = "eb354397a6fc5293"  # first 16 hex of claimcheck_v1.json when it was frozen


def wilson(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval: honest for small n and rates near 0 or 1."""
    if n == 0:
        return (0.0, 0.0)
    p = successes / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (round(max(0.0, centre - half), 3), round(min(1.0, centre + half), 3))


def rate(hits: int, n: int) -> dict:
    low, high = wilson(hits, n)
    return {"hits": hits, "n": n, "rate": round(hits / n, 3) if n else 0.0, "ci95_low": low, "ci95_high": high}


def score(path: Path) -> list[dict]:
    rows = []
    for case in json.loads(path.read_text(encoding="utf-8"))["cases"]:
        result = check_claim(case["draft"], [EvidenceLine(e["id"], e["text"]) for e in case["evidence"]])
        blocked = not result.passed
        rows.append(
            {
                "id": case["id"],
                "category": case["category"],
                "expected": case["expected"],
                "blocked": blocked,
                "correct": blocked == (case["expected"] == "block"),
                "issues": result.issues,
            }
        )
    return rows


def summary(rows: list[dict]) -> dict:
    overstated = [r for r in rows if r["expected"] == "block"]
    honest = [r for r in rows if r["expected"] == "pass"]
    return {
        "block_rate": rate(sum(r["blocked"] for r in overstated), len(overstated)),
        "false_block_rate": rate(sum(r["blocked"] for r in honest), len(honest)),
    }


def evaluate() -> dict:
    raw = DATA.read_bytes()
    data = json.loads(raw)
    rows = score(DATA)
    before = json.loads(BEFORE.read_text(encoding="utf-8"))

    overstated = [r for r in rows if r["expected"] == "block"]
    honest = [r for r in rows if r["expected"] == "pass"]
    by_category: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_category[r["category"]].append(r)

    return {
        "meta": {
            "dataset": data["name"],
            "sha256": hashlib.sha256(raw).hexdigest(),
            "label_status": data["label_status"],
            "package_version": __version__,
        },
        "block_rate": rate(sum(r["blocked"] for r in overstated), len(overstated)),
        "false_block_rate": rate(sum(r["blocked"] for r in honest), len(honest)),
        "categories": {
            name: {
                "expected": items[0]["expected"],
                **rate(sum(r["blocked"] for r in items), len(items)),
            }
            for name, items in sorted(by_category.items(), key=lambda kv: (kv[1][0]["expected"], kv[0]))
        },
        "errors": [r for r in rows if not r["correct"]],
        "cases": rows,
        "before": {"checker": before["checker"], **summary(before["rows"])},
        "dev_claimcheck_v0": summary(score(DEV)),
    }


CATEGORY_LABEL = {
    "verb_synonym": "Stronger verb (synonyms: steered, chaired…)",
    "team_to_sole": "Team work claimed alone",
    "scope_present": "Scope word that is in the evidence",
    "outcome_present": "Outcome that is in the evidence",
    "outcome_placeholder": "Outcome as a placeholder",
    "team_kept": "Team work, team kept",
    "verb_escalation": "Stronger verb (common words)",
    "new_number": "Invented number",
    "changed_number": "Changed number",
    "new_tool": "Invented tool",
    "scope_words": "Wider scope, no new number (production, all, end-to-end)",
    "invented_outcome": "Invented outcome, no number (significantly reduced…)",
    "faithful_rewording": "Faithful rewording",
    "weaker_claim": "Same or weaker claim",
    "placeholders": "Placeholders for missing facts",
    "number_format": "Same number, different format",
    "tool_alias": "Same tool, different name",
}


def render_markdown(r: dict) -> str:
    meta, b, f, before, dev = r["meta"], r["block_rate"], r["false_block_rate"], r["before"], r["dev_claimcheck_v0"]
    data = {c["id"]: c for c in json.loads(DATA.read_text(encoding="utf-8"))["cases"]}
    lines = [
        "# Claim checker report: check_claim v1 on held-out claimcheck_v1",
        "",
        f"Test set `{meta['dataset']}` · sha256 `{meta['sha256'][:12]}` · labels {meta['label_status']} "
        f"· package {meta['package_version']}",
        "",
        "> **Provisional.** Cases and labels were drafted by an AI assistant that also wrote checker v1, and have not",
        "> had a human review. claimcheck_v1 was written and frozen before any v1 change, and only its totals under",
        "> the old checker were looked at before the change. Hard cases were included on purpose.",
        "",
        "The claim checker is the gate between a drafted bullet and approval. It must block drafts that claim more",
        "than the cited evidence shows, and let honest rewrites through.",
        "",
        "| Measure | Result | 95% CI |",
        "| --- | --- | --- |",
        f"| Overstated drafts blocked | {b['hits']}/{b['n']} ({b['rate']:.0%}) | {b['ci95_low']:.0%}–{b['ci95_high']:.0%} |",
        f"| Honest drafts wrongly blocked | {f['hits']}/{f['n']} ({f['rate']:.0%}) | {f['ci95_low']:.0%}–{f['ci95_high']:.0%} |",
        "",
        "Before and after, on the same held-out set:",
        "",
        "| Checker | Overstated blocked | Honest wrongly blocked |",
        "| --- | --- | --- |",
        f"| v0 ({before['checker']}) | {before['block_rate']['hits']}/{before['block_rate']['n']} "
        f"({before['block_rate']['rate']:.0%}) | {before['false_block_rate']['hits']}/{before['false_block_rate']['n']} "
        f"({before['false_block_rate']['rate']:.0%}) |",
        f"| **v1 (current)** | **{b['hits']}/{b['n']} ({b['rate']:.0%})** | **{f['hits']}/{f['n']} ({f['rate']:.0%})** |",
        "",
        f"On claimcheck_v0, which v1 was designed on, v1 blocks {dev['block_rate']['hits']}/{dev['block_rate']['n']} and wrongly "
        f"blocks {dev['false_block_rate']['hits']}/{dev['false_block_rate']['n']}. That is development data, so it shows the "
        "rules do what they were built for, not how well they generalise; the held-out numbers above do.",
        "",
        "## By category",
        "",
        "| Category | Should | Blocked |",
        "| --- | --- | --- |",
    ]
    for name, c in r["categories"].items():
        lines.append(f"| {CATEGORY_LABEL.get(name, name)} | {c['expected']} | {c['hits']}/{c['n']} |")
    lines += [
        "",
        "## Every error",
        "",
        "| Case | Category | Should | Evidence | Draft | Checker said |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for e in r["errors"]:
        case = data[e["id"]]
        evidence = " / ".join(x["text"] for x in case["evidence"])
        said = "; ".join(e["issues"]) if e["issues"] else "passed"
        cells = [e["id"], e["category"], e["expected"], evidence, case["draft"], said]
        lines.append("| " + " | ".join(c.replace("|", "\\|") for c in cells) + " |")
    lines += ["", "Reproduce: `python evals/run_claimcheck.py --check`", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if hashlib.sha256(DATA.read_bytes()).hexdigest()[:16] != FROZEN_SHA256:
        print("claimcheck_v1.json changed since it was frozen. A changed test set needs a new version.")
        return 1
    result = evaluate()

    if args.check:
        committed = json.loads((OUT_DIR / "results.json").read_text(encoding="utf-8"))
        if committed != json.loads(json.dumps(result)):
            print("Claim-check results differ from the committed report.")
            return 1
        print("Claim-check report reproduced exactly.")
        return 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "results.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report = render_markdown(result)
    notes = OUT_DIR / "NOTES.md"
    if notes.exists():
        report += "\n" + notes.read_text(encoding="utf-8")
    (OUT_DIR / "REPORT.md").write_text(report, encoding="utf-8")
    b, f = result["block_rate"], result["false_block_rate"]
    print(f"Blocked {b['hits']}/{b['n']} overstated; wrongly blocked {f['hits']}/{f['n']} honest.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

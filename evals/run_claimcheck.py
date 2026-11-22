"""Held-out evaluation of the claim checker (check_claim) on claimcheck_v0.

Usage (from the repository root):

    python evals/run_claimcheck.py            # writes evals/reports/claimcheck_v0/
    python evals/run_claimcheck.py --check    # CI: fail if results differ from the report

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
DATA = ROOT / "evals" / "datasets" / "claimcheck_v0.json"
OUT_DIR = ROOT / "evals" / "reports" / "claimcheck_v0"
FROZEN_SHA256 = "4634e93fb6cde4d2"  # first 16 hex of claimcheck_v0.json when it was frozen


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


def evaluate() -> dict:
    raw = DATA.read_bytes()
    data = json.loads(raw)
    rows = []
    for case in data["cases"]:
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
    }


CATEGORY_LABEL = {
    "verb_escalation": "Stronger verb (common words)",
    "verb_synonym": "Stronger verb (synonyms: spearheaded, drove…)",
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
    meta, b, f = r["meta"], r["block_rate"], r["false_block_rate"]
    data = {c["id"]: c for c in json.loads(DATA.read_text(encoding="utf-8"))["cases"]}
    lines = [
        "# Claim checker report: check_claim on claimcheck_v0",
        "",
        f"Test set `{meta['dataset']}` · sha256 `{meta['sha256'][:12]}` · labels {meta['label_status']} "
        f"· package {meta['package_version']}",
        "",
        "> **Provisional.** Cases and labels were drafted by an AI assistant that also knew how the checker works,",
        "> and have not had a human review. The set was frozen before the checker was run on it, and the checker",
        "> was not changed afterwards. Categories the checker was expected to miss were included on purpose.",
        "",
        "The claim checker is the gate between a drafted bullet and approval. It must block drafts that claim more",
        "than the cited evidence shows, and let honest rewrites through.",
        "",
        "| Measure | Result | 95% CI |",
        "| --- | --- | --- |",
        f"| Overstated drafts blocked | {b['hits']}/{b['n']} ({b['rate']:.0%}) | {b['ci95_low']:.0%}–{b['ci95_high']:.0%} |",
        f"| Honest drafts wrongly blocked | {f['hits']}/{f['n']} ({f['rate']:.0%}) | {f['ci95_low']:.0%}–{f['ci95_high']:.0%} |",
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
        print("claimcheck_v0.json changed since it was frozen. A changed test set needs a new version.")
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

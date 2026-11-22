"""Live drafting evaluation: what the real model writes, and what the checker does with it.

Usage (from the repository root, with your own key; costs well under $0.10):

    export ANTHROPIC_API_KEY=sk-ant-...
    python evals/run_drafting_eval.py            # writes evals/reports/drafting_v0/ and an audit sheet

    python evals/run_drafting_eval.py --fake --out /tmp/x   # no key, no cost: a scripted model (tests)

Each case in drafting_v0 gives the model a requirement that asks for more than the
evidence shows ("Lead the deployment…" against "Contributed to deploying…"). The
production path runs unchanged: draft, check_claim, one retry with the problems,
else the rule-based shape. The report measures:

* unsupported-claim rate of first drafts, as judged by check_claim, by problem type
* how often the retry fixes a blocked draft, and how often the fallback is used
* a human audit (evals/review/review_drafting_v0.csv) of every model draft that
  passed, because the checker cannot see overstatement it has no rule for

Model output is not deterministic, so this is a dated measurement, not a CI check.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from resumeiq_api import __version__
from resumeiq_api.rewrite import DailyBudget, EvidenceLine, anthropic_completion, configured_temperature, rewrite

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "evals" / "datasets" / "drafting_v0.json"
OUT_DIR = ROOT / "evals" / "reports" / "drafting_v0"
AUDIT = ROOT / "evals" / "review" / "review_drafting_v0.csv"

ISSUE_TYPES = [
    ("It claims", "stronger verb"),
    ("Your evidence describes team work", "team work claimed alone"),
    ("Numbers not", "invented number"),
    ("Tools not", "invented tool"),
    ("Wider scope", "wider scope"),
    ("Outcome not", "invented outcome"),
    ("Keep the bullet under", "too long"),
]


def issue_type(issue: str) -> str:
    return next((label for prefix, label in ISSUE_TYPES if issue.startswith(prefix)), "other")


def fake_completion():
    """Scripted model for tests: overstates on the first attempt, complies on the retry."""

    def call(system: str, user: str) -> str:
        evidence = user.split('">', 1)[1].split("</evidence>", 1)[0]
        if "previous draft was rejected" in user:
            return json.dumps({"bullet": f"{evidence.rstrip('. ')}, [add measurable result]"})
        return json.dumps({"bullet": f"Led {evidence[0].lower()}{evidence[1:].rstrip('. ')}, cutting costs by 40%."})

    return call


def evaluate(cases: list[dict], complete) -> list[dict]:
    rows = []
    for case in cases:
        trace: list[dict] = []
        evidence = [EvidenceLine(e["id"], e["text"]) for e in case["evidence"]]
        result = rewrite(case["requirement"], evidence, complete, DailyBudget(10_000), trace=trace)
        rows.append(
            {
                "id": case["id"],
                "pressure": case["pressure"],
                "attempts": trace,
                "final": result.bullet,
                "source": result.source,
            }
        )
    return rows


def summarise(rows: list[dict]) -> dict:
    first = [r["attempts"][0] for r in rows if r["attempts"] and "draft" in r["attempts"][0]]
    blocked_first = [a for a in first if not a["passed"]]
    retried = [r for r in rows if len(r["attempts"]) == 2 and "draft" in r["attempts"][1]]
    by_type = Counter(t for a in blocked_first for t in {issue_type(i) for i in a["issues"]})
    by_pressure: dict[str, dict[str, int]] = {}
    for r in rows:
        if r["attempts"] and "draft" in r["attempts"][0]:
            entry = by_pressure.setdefault(r["pressure"], {"n": 0, "first_blocked": 0})
            entry["n"] += 1
            entry["first_blocked"] += int(not r["attempts"][0]["passed"])
    return {
        "cases": len(rows),
        "first_drafts": len(first),
        "first_drafts_blocked": len(blocked_first),
        "blocked_by_problem": dict(by_type.most_common()),
        "retries": len(retried),
        "retries_passed": sum(r["attempts"][1]["passed"] for r in retried),
        "final_model_drafts": sum(r["source"] == "model" for r in rows),
        "fallbacks": sum(r["source"] == "rules" for r in rows),
        "api_errors": sum(1 for r in rows for a in r["attempts"] if "error" in a),
        "by_pressure": by_pressure,
    }


def render(meta: dict, s: dict, rows: list[dict], cases: dict) -> str:
    pct = lambda a, b: f"{a}/{b} ({a / b:.0%})" if b else "0/0"  # noqa: E731
    lines = [
        "# Live drafting report: drafting_v0",
        "",
        f"Model `{meta['model']}` · temperature {meta['temperature'] if meta['temperature'] is not None else 'model default'} "
        f"· run {meta['run_at']} · package {meta['package_version']}"
        + (" · **FAKE MODEL (test run)**" if meta["fake"] else ""),
        "",
        "Every requirement except the neutral ones asks for more than its evidence shows, so the model is tempted",
        "to overstate. The production path ran unchanged: draft → check → one retry → rule-based fallback.",
        "",
        "| Measure | Result |",
        "| --- | --- |",
        f"| First drafts blocked by the checker (unsupported-claim rate) | {pct(s['first_drafts_blocked'], s['first_drafts'])} |",
        f"| Blocked drafts fixed by the one retry | {pct(s['retries_passed'], s['retries'])} |",
        f"| Final bullet came from the model | {pct(s['final_model_drafts'], s['cases'])} |",
        f"| Fell back to the rule-based shape | {pct(s['fallbacks'], s['cases'])} |",
        f"| API errors | {s['api_errors']} |",
        "",
        "## Why first drafts were blocked",
        "",
        "| Problem | First drafts |",
        "| --- | --- |",
    ]
    lines += [f"| {k} | {v} |" for k, v in s["blocked_by_problem"].items()] or ["| none | 0 |"]
    lines += ["", "## By kind of pressure", "", "| Pressure | First drafts blocked |", "| --- | --- |"]
    lines += [f"| {k} | {pct(v['first_blocked'], v['n'])} |" for k, v in sorted(s["by_pressure"].items())]
    lines += [
        "",
        "## Human audit",
        "",
        "The checker only catches what it has rules for. Every final model draft is listed in",
        "`evals/review/review_drafting_v0.csv` for a person to mark `honest` or `overstates`; run",
        "`python evals/review/heldout_review.py` afterwards to add the result here.",
        "",
        "## Every case",
        "",
        "| Case | Pressure | Evidence | First draft | Checker | Final |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        case = cases[r["id"]]
        first = r["attempts"][0] if r["attempts"] else {}
        verdict = (
            "error" if "error" in first else ("passed" if first.get("passed") else "; ".join(first.get("issues", [])))
        )
        cells = [
            r["id"],
            r["pressure"],
            case["evidence"][0]["text"],
            first.get("draft", "—"),
            verdict,
            f"{r['final']} ({r['source']})",
        ]
        lines.append("| " + " | ".join(c.replace("|", "\\|") for c in cells) + " |")
    return "\n".join(lines) + "\n"


def write_audit(rows: list[dict], cases: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["case_id", "requirement", "evidence", "final_draft", "source", "your_verdict", "note"])
        for r in rows:
            if r["source"] != "model":
                continue  # the rule-based shape copies the evidence; nothing to audit
            case = cases[r["id"]]
            evidence = " / ".join(e["text"] for e in case["evidence"])
            writer.writerow([r["id"], case["requirement"], evidence, r["final"], r["source"], "", ""])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fake", action="store_true", help="scripted model, no key, no cost")
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    parser.add_argument("--model", default=os.environ.get("RESUMEIQ_LLM_MODEL", "claude-haiku-5-5"))
    args = parser.parse_args(argv)

    if args.fake:
        complete, model = fake_completion(), "fake"
    else:
        key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        if not key:
            print("Set ANTHROPIC_API_KEY first (see docs/v2/MILESTONE_3.md). Nothing was sent.")
            return 2
        complete, model = anthropic_completion(key, args.model, temperature=configured_temperature()), args.model

    return run(complete, model, args.out, args.fake)


def run(complete, model: str, out: Path, fake: bool) -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    cases = {c["id"]: c for c in data["cases"]}
    rows = evaluate(data["cases"], complete)
    summary = summarise(rows)
    if summary["first_drafts"] == 0:
        first_error = next((a["error"] for r in rows for a in r["attempts"] if "error" in a), "no attempt was made")
        print(f"Every model call failed ({first_error}). No report was written; fix the cause and run again.")
        return 1
    meta = {
        "dataset": data["name"],
        "model": model,
        "run_at": datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
        "package_version": __version__,
        "fake": fake,
        "temperature": None if fake else configured_temperature(),
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(
        json.dumps({"meta": meta, "summary": summary, "rows": rows}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (out / "REPORT.md").write_text(render(meta, summary, rows, cases), encoding="utf-8")
    write_audit(rows, cases, out / "audit.csv" if fake else AUDIT)
    print(
        f"First drafts blocked {summary['first_drafts_blocked']}/{summary['first_drafts']}; "
        f"retries fixed {summary['retries_passed']}/{summary['retries']}; fallbacks {summary['fallbacks']}/{summary['cases']}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

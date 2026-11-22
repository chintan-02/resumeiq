"""Human review of the frozen, held-out sets, without editing them.

    python evals/review/heldout_review.py make                       # write the review sheets
    python evals/review/heldout_review.py apply --reviewer "Your Name"  # after you fill them in

Sheets (open in Numbers, Excel or Google Sheets, save back as CSV with the same name):

* review_eval_v1.csv: requirement-to-evidence labels. In your_status write `ok` to agree, or the
  correct status (supported / partial / not_found) with a one-line note.
* review_claimcheck_v2.csv: claim-checker labels. In your_verdict write `ok` to agree, or the correct
  expectation (block / pass) with a note.
* review_drafting_v0.csv / review_drafting_v1.csv: written by run_drafting_eval.py. In your_verdict write `honest` or
  `overstates` for each model draft that passed the checker.

The datasets stay frozen (their hashes are checked by CI). Verdicts are saved to
evals/review/verdicts/ and summarised in evals/reports/heldout_review.md, with every score
recomputed under the reviewer's labels wherever they differ.
"""

from __future__ import annotations

import argparse
import csv
import dataclasses
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "evals"), str(ROOT / "evals" / "review")]

from make_review_sheets import rows as eval_rows  # noqa: E402
from make_review_sheets import write  # noqa: E402

REVIEW = ROOT / "evals" / "review"
VERDICTS = REVIEW / "verdicts"
REPORT = ROOT / "evals" / "reports" / "heldout_review.md"
EVAL_V1 = ROOT / "evals" / "datasets" / "eval_v1.json"
CLAIMCHECK = ROOT / "evals" / "datasets" / "claimcheck_v2.json"  # the current held-out set
STATUSES = {"supported", "partial", "not_found"}


def make(review_dir: Path = REVIEW) -> None:
    records = eval_rows(json.loads(EVAL_V1.read_text(encoding="utf-8")))
    sheet = [{**r, "your_status": "", "note": ""} for r in records]
    write(review_dir / "review_eval_v1.csv", sheet, list(sheet[0]))

    claims = []
    for c in json.loads(CLAIMCHECK.read_text(encoding="utf-8"))["cases"]:
        claims.append(
            {
                "case_id": c["id"],
                "category": c["category"],
                "requirement": c.get("requirement", ""),
                "evidence": " / ".join(e["text"] for e in c["evidence"]),
                "draft": c["draft"],
                "draft_label": c["expected"],
                "why": c["why"],
                "your_verdict": "",
                "note": "",
            }
        )
    write(review_dir / "review_claimcheck_v2.csv", claims, list(claims[0]))
    print(f"Wrote review_eval_v1.csv ({len(sheet)} rows) and review_claimcheck_v2.csv ({len(claims)} rows).")


def _read(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def review_eval_v1(path: Path) -> dict:
    verdicts, problems = {}, []
    for row in _read(path):
        answer = (row.get("your_status") or "").strip().lower()
        if not answer:
            problems.append(row["case_id"])  # not reviewed: excluded, never counted as agreement
        elif answer == "ok":
            verdicts[row["case_id"]] = {"agree": True, "status": row["draft_status"], "note": row.get("note", "")}
        elif answer in STATUSES:
            agree = answer == row["draft_status"]
            verdicts[row["case_id"]] = {"agree": agree, "status": answer, "note": row.get("note", "")}
        else:
            raise SystemExit(
                f"{row['case_id']}: your_status must be ok, supported, partial or not_found, not {answer!r}."
            )
    return {"verdicts": verdicts, "unanswered": problems}


def review_claims(path: Path) -> dict:
    verdicts, problems = {}, []
    for row in _read(path):
        answer = (row.get("your_verdict") or "").strip().lower()
        if not answer:
            problems.append(row["case_id"])  # not reviewed
        elif answer == "ok":
            verdicts[row["case_id"]] = {"agree": True, "expected": row["draft_label"], "note": row.get("note", "")}
        elif answer in ("block", "pass"):
            verdicts[row["case_id"]] = {
                "agree": answer == row["draft_label"],
                "expected": answer,
                "note": row.get("note", ""),
            }
        else:
            raise SystemExit(f"{row['case_id']}: your_verdict must be ok, block or pass, not {answer!r}.")
    return {"verdicts": verdicts, "unanswered": problems}


def review_drafts(path: Path) -> dict:
    verdicts, problems = {}, []
    for row in _read(path):
        answer = (row.get("your_verdict") or "").strip().lower()
        if answer not in ("honest", "overstates"):
            problems.append(row["case_id"])
            continue
        verdicts[row["case_id"]] = {"verdict": answer, "draft": row["final_draft"], "note": row.get("note", "")}
    return {"verdicts": verdicts, "unanswered": problems}


def rescore_eval_v1(verdicts: dict) -> dict:
    """Macro-F1 of the live matcher under the reviewer's labels (same thresholds as the report)."""
    from run_eval_v1 import DEV, TEST

    from resumeiq_api.evaluation import load_cases, macro_f1, predict, tune
    from resumeiq_api.matching import build_matcher

    dev = load_cases(DEV, "dev") + load_cases(DEV, "test")
    thresholds, _ = tune("keyword-rules-v2", dev)
    matcher = build_matcher("keyword-rules-v2", thresholds)
    cases = load_cases(TEST, "test")
    reviewed = [dataclasses.replace(c, gold_status=verdicts[c.id]["status"]) if c.id in verdicts else c for c in cases]
    return {
        "draft_labels": round(macro_f1(predict(matcher, cases)), 3),
        "reviewed_labels": round(macro_f1(predict(matcher, reviewed)), 3),
    }


def rescore_claims(verdicts: dict) -> dict:
    from run_claimcheck import score  # the current checker, on the set this sheet was made from

    rows = score(CLAIMCHECK)
    out = {}
    for name, label in (
        ("draft_labels", lambda r: r["expected"]),
        ("reviewed_labels", lambda r: verdicts.get(r["id"], {"expected": r["expected"]})["expected"]),
    ):
        over = [r for r in rows if label(r) == "block"]
        honest = [r for r in rows if label(r) == "pass"]
        out[name] = {
            "blocked": f"{sum(r['blocked'] for r in over)}/{len(over)}",
            "wrongly_blocked": f"{sum(r['blocked'] for r in honest)}/{len(honest)}",
        }
    return out


AI_NOTE = [
    "> **This is an AI second pass, not a human review.** The verdicts were written by an AI assistant re-reading",
    "> labels it had drafted itself. A second pass can catch inconsistencies (it changed one label here), but it shares",
    "> the author's blind spots, so the labels stay provisional until a person reviews them.",
    "",
]


def apply(
    reviewer: str, review_dir: Path = REVIEW, verdict_dir: Path = VERDICTS, report: Path = REPORT, ai: bool = False
) -> str:
    verdict_dir.mkdir(parents=True, exist_ok=True)
    date = datetime.now(UTC).strftime("%Y-%m-%d")
    title = "# AI second-pass review of the held-out sets" if ai else "# Human review of the held-out sets"
    lines = [title, "", f"Reviewer: {reviewer} · {date}", "", *(AI_NOTE if ai else [])]
    found = False

    sheet = review_dir / "review_eval_v1.csv"
    if sheet.exists():
        found = True
        r = review_eval_v1(sheet)
        agree = sum(v["agree"] for v in r["verdicts"].values())
        scores = rescore_eval_v1(r["verdicts"])
        lines += [
            "## eval_v1 (matching labels)",
            "",
            f"Reviewed {len(r['verdicts'])}/{len(r['verdicts']) + len(r['unanswered'])}; agreed with {agree}. Matcher v2 macro-F1: {scores['draft_labels']} on the drafted "
            f"labels, {scores['reviewed_labels']} on the reviewed labels.",
        ]
        lines += _disagreements({k: v for k, v in r["verdicts"].items() if not v["agree"]}, "status")
        lines += _unanswered(r["unanswered"])
        (verdict_dir / "eval_v1.json").write_text(
            json.dumps({"reviewer": reviewer, "date": date, **r}, indent=2) + "\n"
        )

    sheet = review_dir / "review_claimcheck_v2.csv"
    if sheet.exists():
        found = True
        r = review_claims(sheet)
        agree = sum(v["agree"] for v in r["verdicts"].values())
        scores = rescore_claims(r["verdicts"])
        lines += [
            "",
            "## claimcheck_v2 (claim-checker labels)",
            "",
            f"Reviewed {len(r['verdicts'])}/{len(r['verdicts']) + len(r['unanswered'])}; agreed with {agree}. Current checker on drafted labels: blocked "
            f"{scores['draft_labels']['blocked']}, wrongly blocked {scores['draft_labels']['wrongly_blocked']}. "
            f"On reviewed labels: blocked {scores['reviewed_labels']['blocked']}, wrongly blocked "
            f"{scores['reviewed_labels']['wrongly_blocked']}.",
        ]
        lines += _disagreements({k: v for k, v in r["verdicts"].items() if not v["agree"]}, "expected")
        lines += _unanswered(r["unanswered"])
        (verdict_dir / "claimcheck_v2.json").write_text(
            json.dumps({"reviewer": reviewer, "date": date, **r}, indent=2) + "\n"
        )

    for version in ("v0", "v1"):
        sheet = review_dir / f"review_drafting_{version}.csv"
        if not sheet.exists():
            continue
        found = True
        r = review_drafts(sheet)
        over = {k: v for k, v in r["verdicts"].items() if v["verdict"] == "overstates"}
        lines += [
            "",
            f"## drafting_{version} (audit of model drafts that passed the checker)",
            "",
            f"{len(over)} of {len(r['verdicts'])} audited model drafts overstate their evidence in the reviewer's judgement. "
            "These are claims the checker had no rule for.",
        ]
        lines += [f"- {k}: {v['draft']}" + (f" ({v['note']})" if v["note"] else "") for k, v in over.items()]
        lines += _unanswered(r["unanswered"])
        (verdict_dir / f"drafting_{version}.json").write_text(
            json.dumps({"reviewer": reviewer, "date": date, **r}, indent=2) + "\n"
        )

    if not found:
        raise SystemExit("No filled review sheets found. Run `make` and fill them in first.")
    text = "\n".join(lines) + "\n"
    report.write_text(text, encoding="utf-8")
    return text


def _disagreements(items: dict, field: str) -> list[str]:
    if not items:
        return ["", "No disagreements."]
    out = ["", "| Case | Reviewer's label | Note |", "| --- | --- | --- |"]
    return out + [f"| {k} | {v[field]} | {v['note'] or ''} |" for k, v in items.items()]


def _unanswered(ids: list[str]) -> list[str]:
    return ["", f"Not reviewed yet (draft label kept): {', '.join(ids)}"] if ids else []


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("make")
    run = sub.add_parser("apply")
    run.add_argument("--reviewer", required=True)
    run.add_argument("--ai", action="store_true", help="the verdicts were written by an AI, not a person")
    args = parser.parse_args()
    if args.command == "make":
        make()
    else:
        print(apply(args.reviewer, ai=args.ai))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

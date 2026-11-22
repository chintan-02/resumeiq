"""Held-out evaluation of matcher v3 on eval_v2.

Usage (from the repository root):

    python evals/run_eval_v2.py            # writes evals/reports/eval_v2/
    python evals/run_eval_v2.py --check    # CI: fail if results differ from the report

Protocol:

* eval_v2 was written and frozen (sha256 recorded below) before any matcher-v3 code.
  matcher v2's totals on it were recorded before v3 existed.
* Every matcher is tuned on eval_v0 (dev and test) plus eval_v1. Both were viewed
  while v3 was designed, so they are development data now.
* Adoption rule, fixed before scoring: adopt v3 if it is no worse than v2 on dev
  and fixes the cross-line class (a skill listed in one line lifted by a strong verb
  in another). eval_v2 is scored once and is never used for tuning.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from resumeiq_api import __version__
from resumeiq_api.evaluation import dataset_sha256, full_report, load_cases, predict, tune
from resumeiq_api.fitmap import TUNED_THRESHOLDS_PATH
from resumeiq_api.matching import build_matcher

ROOT = Path(__file__).resolve().parents[1]
DEV_V0 = ROOT / "evals" / "datasets" / "eval_v0.json"
DEV_V1 = ROOT / "evals" / "datasets" / "eval_v1.json"
TEST = ROOT / "evals" / "datasets" / "eval_v2.json"
OUT_DIR = ROOT / "evals" / "reports" / "eval_v2"
MATCHERS = ["keyword-rules-v2", "keyword-rules-v3"]
FROZEN_SHA256 = "5ef74f0771f9baa4"  # first 16 hex of eval_v2.json when it was frozen


def dev_cases():
    return load_cases(DEV_V0, "dev") + load_cases(DEV_V0, "test") + load_cases(DEV_V1, "test")


def evaluate(name: str) -> dict:
    dev = dev_cases()
    thresholds, dev_score = tune(name, dev)
    matcher = build_matcher(name, thresholds)
    data = json.loads(TEST.read_text(encoding="utf-8"))
    labels = [c["label_status"] for c in data["cases"]]
    return {
        "matcher": name,
        "meta": {
            "test_dataset": data["name"],
            "test_sha256": dataset_sha256(TEST),
            "dev_dataset": "eval_v0 (dev + test) + eval_v1",
            "dev_sha256": [dataset_sha256(DEV_V0), dataset_sha256(DEV_V1)],
            "guide_version": data["guide_version"],
            "label_status": {s: labels.count(s) for s in sorted(set(labels))},
            "package_version": __version__,
        },
        "thresholds": {"low": thresholds.low, "high": thresholds.high},
        "dev_macro_f1_at_tuning": dev_score,
        "dev": full_report(predict(matcher, dev)),
        "test": full_report(predict(matcher, load_cases(TEST, "test"))),
    }


MISS_NOTES = {
    "C12-J7-R4": "Strong verb, wrong work: 'Led the quarterly inventory planning process' is read as leading.",
    "C14-J8-R4": "Strong verb, wrong work: 'Responsible for monitoring the office network' is read as owning monitoring.",
    "C14-J8-R3": "Built REST endpoints, but not for model serving; keywords cannot see the missing purpose.",
    "C12-J7-R5": "Excel reports are a related tool (partial); v3 sees Looker only listed and says not found.",
    "C13-J8-R6": "Pairing with one graduate is mentoring-like (partial, ambiguous); no keyword overlap.",
}


def render_markdown(results: list[dict]) -> str:
    meta = results[0]["meta"]
    n = results[0]["test"]["n"]
    lines = [
        "# Held-out report: matcher v3 on eval_v2",
        "",
        f"Test set `{meta['test_dataset']}` · sha256 `{meta['test_sha256'][:12]}` · labels {meta['label_status']} "
        f"· labelling guide v{meta['guide_version']} · package {meta['package_version']}",
        "",
        "> **Provisional.** Labels were drafted by an AI assistant and have not had a human review. The same author",
        "> wrote the test set and matcher v3, which makes these numbers optimistic. The set was frozen before any v3",
        f"> code and no threshold or rule was tuned on it. {n} cases is small, so the confidence intervals are wide",
        "> and overlap: read the difference as direction, not proof.",
        "",
        "**What v3 changes.** v2 judged strength from the strongest cited line, so `Skills: Looker` plus an",
        "unrelated `Built weekly sales reports` could read as building Looker dashboards. v3 judges each named",
        "tool or skill in the requirement (words the posting capitalises: Airflow, SQL, Docker) by the best line",
        "that actually mentions it, and the requirement by the weakest of those. Generic words (data, model, test)",
        "keep v2's rule, because an early version that judged them too lost accuracy on dev.",
        "",
        "| Matcher | Dev macro-F1 | Held-out macro-F1 [95% CI] | Accuracy | Trap cases correct | Evidence recall@3 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for r in results:
        t = r["test"]
        ci = t["macro_f1_bootstrap"]
        lines.append(
            f"| `{r['matcher']}` | {r['dev']['macro_f1']:.2f} | {t['macro_f1']:.2f} [{ci['ci95_low']:.2f}, "
            f"{ci['ci95_high']:.2f}] | {t['accuracy']:.2f} | {t['trap_accuracy']['correct']}/"
            f"{t['trap_accuracy']['n']} | {t['evidence_recall'][1]['recall']:.2f} |"
        )
    v3 = next(r for r in results if r["matcher"] == "keyword-rules-v3")
    lines += [
        "",
        "Thresholds (tuned on dev): "
        + ", ".join(f"`{r['matcher']}` low {r['thresholds']['low']}, high {r['thresholds']['high']}" for r in results),
        "",
        "Decision: v3 changed 2 of 90 dev answers, both toward the gold label, and none away from it, so it met",
        "the adoption rule. It is the default matcher from this release; v2 stays in the code for comparison.",
        "",
        "## Errors of `keyword-rules-v3` on eval_v2",
        "",
        "| Case | Gold | Predicted | Why |",
        "| --- | --- | --- | --- |",
    ]
    for e in v3["test"]["errors"]:
        lines.append(f"| {e['case']} | {e['gold']} | {e['predicted']} | {MISS_NOTES.get(e['case'], '')} |")
    lines += [
        "",
        "Trap accuracy did not move (9/12 for both). Two of the three trap misses are a different failure: a",
        "strong verb attached to the wrong work. Telling 'led inventory planning' from 'led a data platform",
        "migration' needs the object of the verb, which a keyword matcher does not read. That is the next",
        "target, and it needs a new frozen set when it is attempted. The third (C12-J7-R5) is v3 being stricter",
        "than the guide: a related tool (Excel for Looker) counts as partial, and v3 does not know tools are related.",
        "",
        "Reproduce: `python evals/run_eval_v2.py --check`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if dataset_sha256(TEST)[:16] != FROZEN_SHA256:
        print("eval_v2.json changed since it was frozen. A changed test set needs a new version (eval_v3).")
        return 1
    results = [evaluate(name) for name in MATCHERS]

    if args.check:
        mismatched = []
        for r in results:
            committed = json.loads((OUT_DIR / f"{r['matcher']}.json").read_text(encoding="utf-8"))
            if committed != json.loads(json.dumps(r)):
                mismatched.append(r["matcher"])
        if mismatched:
            print(f"Results differ from the committed report: {mismatched}.")
            return 1
        print("Held-out report (eval_v2) reproduced exactly.")
        return 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for r in results:
        (OUT_DIR / f"{r['matcher']}.json").write_text(json.dumps(r, indent=2) + "\n", encoding="utf-8")
    (OUT_DIR / "REPORT.md").write_text(render_markdown(results), encoding="utf-8")

    tuned = json.loads(TUNED_THRESHOLDS_PATH.read_text(encoding="utf-8")) if TUNED_THRESHOLDS_PATH.exists() else {}
    tuned["keyword-rules-v3"] = v3_thresholds = next(r for r in results if r["matcher"] == "keyword-rules-v3")[
        "thresholds"
    ]
    TUNED_THRESHOLDS_PATH.write_text(json.dumps(tuned, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print((OUT_DIR / "REPORT.md").read_text(encoding="utf-8"), v3_thresholds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

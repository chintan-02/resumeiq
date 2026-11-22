"""Held-out evaluation of matcher v2 on eval_v1.

Usage (from the repository root):

    python evals/run_eval_v1.py            # writes evals/reports/eval_v1/
    python evals/run_eval_v1.py --check    # CI: fail if results differ from the report

Protocol:

* eval_v1 was written and frozen (sha256 recorded below) before any matcher-v2 code.
* Every matcher is tuned on eval_v0 (dev and test together). eval_v0's test split
  was viewed while v2 was designed, so it is no longer a clean test set; it is
  development data now.
* eval_v1 is scored once with the frozen thresholds and is never used for tuning.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from resumeiq_api import __version__
from resumeiq_api.evaluation import dataset_sha256, full_report, load_cases, predict, tune
from resumeiq_api.fitmap import TUNED_THRESHOLDS_PATH
from resumeiq_api.matching import build_matcher

ROOT = Path(__file__).resolve().parents[1]
DEV = ROOT / "evals" / "datasets" / "eval_v0.json"
TEST = ROOT / "evals" / "datasets" / "eval_v1.json"
OUT_DIR = ROOT / "evals" / "reports" / "eval_v1"
MATCHERS = ["keyword", "keyword-rules", "keyword-rules-v2"]
FROZEN_SHA256 = "a211038541f44fd1"  # first 16 hex of eval_v1.json when it was frozen


def evaluate(name: str) -> dict:
    dev = load_cases(DEV, "dev") + load_cases(DEV, "test")
    test = load_cases(TEST, "test")
    thresholds, dev_score = tune(name, dev)
    matcher = build_matcher(name, thresholds)
    data = json.loads(TEST.read_text(encoding="utf-8"))
    labels = [c["label_status"] for c in data["cases"]]
    return {
        "matcher": name,
        "meta": {
            "test_dataset": data["name"],
            "test_sha256": dataset_sha256(TEST),
            "dev_dataset": "eval_v0 (dev + test)",
            "dev_sha256": dataset_sha256(DEV),
            "guide_version": data["guide_version"],
            "label_status": {s: labels.count(s) for s in sorted(set(labels))},
            "package_version": __version__,
        },
        "thresholds": {"low": thresholds.low, "high": thresholds.high},
        "dev_macro_f1_at_tuning": dev_score,
        "test": full_report(predict(matcher, test)),
    }


def render_markdown(results: list[dict]) -> str:
    meta = results[0]["meta"]
    n = results[0]["test"]["n"]
    lines = [
        "# Held-out report: matcher v2 on eval_v1",
        "",
        f"Test set `{meta['test_dataset']}` · sha256 `{meta['test_sha256'][:12]}` · labels {meta['label_status']} "
        f"· labelling guide v{meta['guide_version']} · package {meta['package_version']}",
        "",
        "> **Provisional.** Labels were drafted by an AI assistant and have not had a human review. The same author",
        "> wrote the test set and matcher v2; the set was written and frozen before any v2 code, and no threshold or",
        f"> rule was tuned on it. {n} cases is small, so the confidence intervals are wide.",
        "",
        "All matchers were tuned on eval_v0 (dev and test together) and scored once on eval_v1, which has new job",
        "families and candidates aimed at v1's known failures: compound requirements, `A/B` and `such as`",
        "alternatives, paraphrases and keyword traps.",
        "",
        "| Matcher | Macro-F1 [95% CI] | Accuracy | Trap cases correct | Evidence recall@1 | Evidence recall@3 | Citation precision |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in results:
        t = r["test"]
        ci = t["macro_f1_bootstrap"]
        r1, r3 = t["evidence_recall"]
        lines.append(
            f"| `{r['matcher']}` | {t['macro_f1']:.2f} [{ci['ci95_low']:.2f}, {ci['ci95_high']:.2f}] | {t['accuracy']:.2f} "
            f"| {t['trap_accuracy']['correct']}/{t['trap_accuracy']['n']} | {r1['recall']:.2f} "
            f"| {r3['recall']:.2f} | {t['citation_precision']['precision']:.2f} |"
        )
    lines += [
        "",
        "Thresholds (tuned on eval_v0): "
        + ", ".join(f"`{r['matcher']}` low {r['thresholds']['low']}, high {r['thresholds']['high']}" for r in results),
        "",
        "## Errors of `keyword-rules-v2` on eval_v1",
        "",
        "| Case | Gold | Predicted |",
        "| --- | --- | --- |",
    ]
    v2 = next(r for r in results if r["matcher"] == "keyword-rules-v2")
    for e in v2["test"]["errors"]:
        lines.append(f"| {e['case']} | {e['gold']} | {e['predicted']} |")
    lines += [
        "",
        "## Run history",
        "",
        "eval_v1 has been scored twice. Run 1 (macro-F1 v2 0.73, v1 0.60, naive 0.49) exposed nothing that was",
        "changed in response. Between runs, a unit test written for the v2 spec found that `FastAPI/Flask` was not",
        "read as either/or (synonym expansion split the option). That bug was fixed, dev scores were unchanged",
        "(eval_v0 macro-F1 0.839, same thresholds), and the table above is run 2. No other change was made.",
        "",
        "Reproduce: `python evals/run_eval_v1.py --check`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if dataset_sha256(TEST)[:16] != FROZEN_SHA256:
        print("eval_v1.json changed since it was frozen. A changed test set needs a new version (eval_v2).")
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
        print("Held-out report reproduced exactly.")
        return 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for r in results:
        (OUT_DIR / f"{r['matcher']}.json").write_text(json.dumps(r, indent=2) + "\n", encoding="utf-8")
    (OUT_DIR / "REPORT.md").write_text(render_markdown(results), encoding="utf-8")

    tuned = json.loads(TUNED_THRESHOLDS_PATH.read_text(encoding="utf-8")) if TUNED_THRESHOLDS_PATH.exists() else {}
    v2 = next(r for r in results if r["matcher"] == "keyword-rules-v2")
    tuned["keyword-rules-v2"] = v2["thresholds"]
    TUNED_THRESHOLDS_PATH.write_text(json.dumps(tuned, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print((OUT_DIR / "REPORT.md").read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())

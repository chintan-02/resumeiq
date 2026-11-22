"""Reproducible baseline evaluation for requirement → evidence matching.

Usage (from the repository root):

    python evals/run_baseline.py                       # keyword baselines, writes the report
    python evals/run_baseline.py --check               # CI: fail if results differ from the report
    python evals/run_baseline.py --matchers embedding embedding-rules   # needs the embeddings extra

Thresholds are tuned on the dev split and then frozen for the test split.
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
DATASET = ROOT / "evals" / "datasets" / "eval_v0.json"
OUT_DIR = ROOT / "evals" / "reports" / "baseline_v0"
KEYWORD_MATCHERS = ["keyword", "keyword-rules"]


def evaluate(name: str) -> dict:
    dev, test = load_cases(DATASET, "dev"), load_cases(DATASET, "test")
    thresholds, dev_score = tune(name, dev)
    matcher = build_matcher(name, thresholds)
    data = json.loads(DATASET.read_text(encoding="utf-8"))
    labels = [c["label_status"] for c in data["cases"]]
    return {
        "matcher": name,
        "meta": {
            "dataset": data["name"],
            "dataset_sha256": dataset_sha256(DATASET),
            "guide_version": data["guide_version"],
            "label_status": {s: labels.count(s) for s in sorted(set(labels))},
            "package_version": __version__,
            "tuned_on": "dev",
        },
        "thresholds": {"low": thresholds.low, "high": thresholds.high},
        "dev_macro_f1_at_tuning": dev_score,
        "dev": full_report(predict(matcher, dev)),
        "test": full_report(predict(matcher, test)),
    }


def _fmt_ci(report: dict) -> str:
    ci = report["macro_f1_bootstrap"]
    return f"{report['macro_f1']:.2f} [{ci['ci95_low']:.2f}, {ci['ci95_high']:.2f}]"


def render_markdown(results: list[dict]) -> str:
    meta = results[0]["meta"]
    n_test, n_dev = results[0]["test"]["n"], results[0]["dev"]["n"]
    lines = [
        "# Baseline report: requirement → evidence matching (eval_v0)",
        "",
        f"Dataset `{meta['dataset']}` · sha256 `{meta['dataset_sha256'][:12]}` · labelling guide v{meta['guide_version']} "
        f"· labels {meta['label_status']} · package {meta['package_version']}",
        "",
        "> **Provisional.** Labels are drafts written by an AI assistant and not yet reviewed by a person.",
        f"> The test split has {n_test} cases (dev: {n_dev}), so confidence intervals are wide. Do not quote these",
        "> numbers publicly until the labels are reviewed and the set is larger.",
        "",
        "Thresholds were tuned on the dev split (candidates C1–C3, job families J1–J2) and frozen before",
        "scoring the test split (C4–C6, J3–J4). Candidates and job families never cross splits.",
        "",
        "## Test split",
        "",
        "| Matcher | Macro-F1 [95% CI] | Accuracy | Trap cases correct | Evidence recall@1 | Evidence recall@3 | Citation precision |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in results:
        t = r["test"]
        rec1, rec3 = t["evidence_recall"]
        cp = t["citation_precision"]
        lines.append(
            f"| `{r['matcher']}` | {_fmt_ci(t)} | {t['accuracy']:.2f} | "
            f"{t['trap_accuracy']['correct']}/{t['trap_accuracy']['n']} | "
            f"{rec1['recall']:.2f} | {rec3['recall']:.2f} | {cp['precision']:.2f} ({cp['correct']}/{cp['cited']}) |"
        )
    lines += [
        "",
        "## Dev split (used for tuning)",
        "",
        "| Matcher | Thresholds (low / high) | Macro-F1 | Trap cases correct |",
        "| --- | --- | --- | --- |",
    ]
    for r in results:
        d = r["dev"]
        lines.append(
            f"| `{r['matcher']}` | {r['thresholds']['low']} / {r['thresholds']['high']} | {d['macro_f1']:.2f} | "
            f"{d['trap_accuracy']['correct']}/{d['trap_accuracy']['n']} |"
        )
    for r in results:
        lines += ["", f"## Test errors: `{r['matcher']}`", ""]
        if not r["test"]["errors"]:
            lines.append("None.")
            continue
        lines += ["| Case | Requirement | Gold | Predicted | Trap |", "| --- | --- | --- | --- | --- |"]
        for e in r["test"]["errors"]:
            lines.append(
                f"| {e['case']} | {e['requirement']} | {e['gold']} | {e['predicted']} | {'yes' if e['trap'] else ''} |"
            )
    lines += [
        "",
        "## Evaluation protocol and known issues",
        "",
        "- The eval_v0 **test split has now been looked at**. Method changes motivated by its errors must be",
        "  measured on a fresh test set (eval_v1), not on this one, or the numbers stop meaning anything.",
        "- Known issues seen in test errors, deliberately **not** fixed against this split:",
        '  - Synonym replacement drops words: "Google Cloud Storage" becomes `gcs`, so "cloud storage" no longer',
        "    matches. Synonyms should add the canonical term and keep the original words.",
        '  - The light stemmer merges unrelated words ("stored" and "stores" both become `stor`), which creates',
        '    a false match for "feature stores".',
        '  - Keyword retrieval cannot connect paraphrases ("Vertex AI" for "the cloud", "GitHub Actions" for',
        '    "CI pipelines"). This is what the embedding comparison is meant to measure.',
        '  - Compound requirements are judged as one unit: "Docker and Kubernetes" counts as supported when the',
        "    evidence says another team did the Kubernetes part.",
        "- The 6 generic-term cases (`*-R9`) were added to both splits after the walkthrough showed a false",
        '  "supported" from a single shared word; see `changelog` in the dataset.',
        "- Embedding matchers need a model download and run on a developer machine:",
        '  `pip install -e "apps/api[embeddings]"` then',
        "  `python evals/run_baseline.py --matchers keyword keyword-rules embedding embedding-rules`.",
        "",
        "## How to read this",
        "",
        "- **Evidence recall@k** checks retrieval: was a gold evidence item among the top k candidates?",
        "- **Macro-F1** and **trap cases** check judgment: given the evidence, was the status right?",
        "  Trap cases contain the right keyword but support a weaker claim or a different meaning.",
        "- **Citation precision**: of the evidence items the matcher cited, how many are gold evidence.",
        "",
        "Reproduce: `python evals/run_baseline.py --check`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matchers", nargs="+", default=KEYWORD_MATCHERS)
    parser.add_argument("--check", action="store_true", help="Fail if fresh results differ from the committed report.")
    args = parser.parse_args()

    results = [evaluate(name) for name in args.matchers]

    if args.check:
        mismatched = []
        for r in results:
            committed_path = OUT_DIR / f"{r['matcher']}.json"
            if not committed_path.exists():
                mismatched.append(f"{r['matcher']}: no committed report")
                continue
            committed = json.loads(committed_path.read_text(encoding="utf-8"))
            if committed != r:
                mismatched.append(r["matcher"])
        if mismatched:
            print(f"Results differ from the committed report: {mismatched}. Re-run without --check and commit.")
            return 1
        print("Baseline report reproduced exactly.")
        return 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for r in results:
        (OUT_DIR / f"{r['matcher']}.json").write_text(json.dumps(r, indent=2) + "\n", encoding="utf-8")
    all_results = [
        json.loads((OUT_DIR / f"{name}.json").read_text(encoding="utf-8"))
        for name in ["keyword", "keyword-rules", "embedding", "embedding-rules"]
        if (OUT_DIR / f"{name}.json").exists()
    ]
    (OUT_DIR / "REPORT.md").write_text(render_markdown(all_results), encoding="utf-8")

    # The API uses the tuned thresholds, so the demo matches the evaluated configuration.
    tuned = json.loads(TUNED_THRESHOLDS_PATH.read_text(encoding="utf-8")) if TUNED_THRESHOLDS_PATH.exists() else {}
    for r in results:
        tuned[r["matcher"]] = r["thresholds"]
    TUNED_THRESHOLDS_PATH.write_text(json.dumps(tuned, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    for r in results:
        t = r["test"]
        print(
            f"{r['matcher']:>16}: test macro-F1 {_fmt_ci(t)} · traps {t['trap_accuracy']['correct']}/{t['trap_accuracy']['n']}"
        )
    print(f"Wrote {OUT_DIR / 'REPORT.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

import importlib.util
import json

from resumeiq_api.evaluation import (
    Case,
    Prediction,
    bootstrap_macro_f1,
    classification_metrics,
    evidence_recall_at_k,
    load_cases,
)
from resumeiq_api.evidence import segment
from resumeiq_api.models import Level, Requirement
from resumeiq_api.samples import load_samples

from .conftest import REPO_ROOT


def _data(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_gold_labels_are_internally_consistent(dataset_path):
    data = _data(dataset_path)
    pools = {cid: {e["id"]: e["text"] for e in c["evidence"]} for cid, c in data["candidates"].items()}
    req_job = {r["id"]: jid for jid, j in data["jobs"].items() for r in j["requirements"]}
    ids = set()
    for case in data["cases"]:
        assert case["id"] not in ids
        ids.add(case["id"])
        pool = pools[case["candidate"]]
        assert req_job[case["requirement"]] == data["candidates"][case["candidate"]]["job"]
        assert case["gold_status"] in {"supported", "partial", "not_found"}
        assert set(case["gold_evidence_ids"]) <= set(pool)
        if case["gold_status"] == "not_found":
            assert case["gold_evidence_ids"] == [] and case["gold_quote"] == ""
        else:
            assert case["gold_evidence_ids"], case["id"]
            assert any(case["gold_quote"] in pool[e] for e in case["gold_evidence_ids"]), case["id"]


def test_splits_never_share_candidates_or_job_families(dataset_path):
    data = _data(dataset_path)
    for cand in data["candidates"].values():
        assert data["jobs"][cand["job"]]["split"] == cand["split"]
    families = {}
    for job in data["jobs"].values():
        families.setdefault(job["family"], set()).add(job["split"])
    assert all(len(splits) == 1 for splits in families.values())


def test_demo_sample_is_not_in_the_evaluation_set(dataset_path):
    data = _data(dataset_path)
    eval_text = " ".join(e["text"] for c in data["candidates"].values() for e in c["evidence"]).lower()
    for sample in load_samples().values():
        for document in sample.documents:
            for item in segment(document):
                assert item.text.lower() not in eval_text, item.text


def _pred(gold, status, ranked=(), gold_ev=()):
    case = Case(
        "c", Requirement(id="r", text="xyz", required_level=Level.USED), (), gold, tuple(gold_ev), False, False, "draft"
    )
    return Prediction(case, status, (), tuple(ranked))


def test_metrics_on_a_hand_checked_example():
    preds = [_pred("supported", "supported"), _pred("partial", "supported"), _pred("not_found", "not_found")]
    m = classification_metrics(preds)
    assert m["accuracy"] == round(2 / 3, 4)
    assert m["per_class"]["supported"] == {"precision": 0.5, "recall": 1.0, "f1": round(2 / 3, 4), "support": 1}
    assert m["per_class"]["partial"]["f1"] == 0.0
    assert evidence_recall_at_k([_pred("supported", "supported", ["b", "a"], ["a"])], 1)["recall"] == 0.0
    assert evidence_recall_at_k([_pred("supported", "supported", ["b", "a"], ["a"])], 3)["recall"] == 1.0


def test_bootstrap_is_deterministic():
    preds = [_pred("supported", "supported"), _pred("partial", "not_found")] * 5
    assert bootstrap_macro_f1(preds) == bootstrap_macro_f1(preds)


def test_both_splits_load(dataset_path):
    assert len(load_cases(dataset_path, "dev")) == 27
    assert len(load_cases(dataset_path, "test")) == 27


def test_committed_baseline_report_reproduces_exactly():
    spec = importlib.util.spec_from_file_location("run_baseline", REPO_ROOT / "evals" / "run_baseline.py")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    for name in runner.KEYWORD_MATCHERS:
        committed = json.loads((runner.OUT_DIR / f"{name}.json").read_text(encoding="utf-8"))
        assert runner.evaluate(name) == committed, f"Re-run `python evals/run_baseline.py` for {name}"

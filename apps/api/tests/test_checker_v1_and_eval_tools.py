"""Checker v1 rules, attempt tracing, and the evaluation tools (drafting runner, review kit)."""

import csv
import json
import sys
from pathlib import Path

import pytest

from resumeiq_api.rewrite import DailyBudget, EvidenceLine, check_claim, rewrite

REPO = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(REPO / "evals"), str(REPO / "evals" / "review")]


def check(draft: str, *evidence: str):
    return check_claim(draft, [EvidenceLine(f"E{i}", t) for i, t in enumerate(evidence)])


@pytest.mark.parametrize(
    ("draft", "evidence"),
    [
        ("Cut spend by 12 % with indexing.", "Cut spend by 12% with indexing."),
        ("Supported 2 product teams.", "Supported two product teams."),
        ("Mentored two interns.", "Mentored 2 interns."),
        ("Wrote tests for all checkout services.", "Wrote tests for all checkout services."),
        ("Presented results every month.", "Presented results to managers every month."),
        ("Presented [model] results to [audience] every [period].", "Presented results to managers."),
        ("Migrated jobs to Airflow, reducing [failure type] by [amount].", "Migrated jobs to Airflow."),
        (
            "Reduced p95 latency from 800 ms to 200 ms with caching.",
            "Added caching, reducing p95 latency from 800 ms to 200 ms.",
        ),
        ("Rebuilt the API as one of four engineers.", "Was one of four engineers who rebuilt the API."),
        ("Led 3 analysts in rebuilding the dashboard.", "Led a team of 3 analysts to rebuild the dashboard."),
    ],
)
def test_honest_drafts_pass_checker_v1(draft, evidence):
    result = check(draft, evidence)
    assert result.passed, result.issues


@pytest.mark.parametrize(
    ("draft", "evidence", "problem"),
    [
        ("Rebuilt the search model.", "Worked on a team that rebuilt the search model.", "team work"),
        ("Orchestrated the retraining.", "Assisted in coordinating the retraining.", "claims ownership"),
        ("Built a production dashboard.", "Built a prototype dashboard.", "Wider scope"),
        ("Built a real-time scoring service.", "Built a batch scoring job.", "Wider scope"),
        ("Rewrote the job in PySpark, dramatically improving reliability.", "Rewrote the job in PySpark.", "Outcome"),
        ("Presented results, leading to a new campaign.", "Presented results to managers.", "Outcome"),
        ("Documented the steps, which sped up onboarding.", "Documented the steps.", "Outcome"),
        ("Mentored five interns.", "Mentored two interns.", "Numbers"),
    ],
)
def test_overstated_drafts_are_blocked_with_a_reason(draft, evidence, problem):
    result = check(draft, evidence)
    assert not result.passed
    assert any(problem in issue for issue in result.issues), result.issues


def test_rule_based_fallback_still_passes_its_own_check():
    for line in [
        "Contributed to the deployment of the forecasting service to Azure with the platform team.",
        "Was one of four engineers who rebuilt the billing API.",
        "Built a prototype churn model in a notebook.",
    ]:
        result = rewrite("Lead deployments", [EvidenceLine("E1", line)], None, DailyBudget(0))
        assert result.source == "rules" and result.check.passed, result.check.issues


def test_trace_records_every_attempt():
    answers = iter(
        [
            '{"bullet": "Led the deployment to AWS."}',
            '{"bullet": "Contributed to the AWS deployment with the platform team."}',
        ]
    )
    trace: list[dict] = []
    result = rewrite(
        "Lead deployments",
        [EvidenceLine("E1", "Contributed to the AWS deployment with the platform team.")],
        lambda system, user: next(answers),
        DailyBudget(5),
        trace=trace,
    )
    assert result.source == "model" and result.attempts == 2
    assert [a["passed"] for a in trace] == [False, True]
    assert "Led the deployment" in trace[0]["draft"]


def test_drafting_runner_works_end_to_end_with_a_fake_model(tmp_path):
    import run_drafting_eval

    assert run_drafting_eval.main(["--set", "v1", "--fake", "--out", str(tmp_path)]) == 0
    summary = json.loads((tmp_path / "results.json").read_text())["summary"]
    assert summary["first_drafts"] == summary["cases"] == 24
    assert summary["first_drafts_blocked"] == 24  # the fake overstates first
    assert summary["retries_passed"] == 24 and summary["fallbacks"] == 0
    assert "FAKE MODEL" in (tmp_path / "REPORT.md").read_text()
    assert len(list(csv.DictReader((tmp_path / "audit.csv").open()))) == 24


def test_drafting_runner_refuses_without_a_key(monkeypatch):
    import run_drafting_eval

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert run_drafting_eval.main([]) == 2


def _fill(src: Path, dst: Path, column: str, answers: dict, default: str) -> None:
    with src.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for row in rows:
        row[column] = answers.get(row["case_id"], default)
    with dst.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_review_kit_keeps_frozen_sets_and_rescores_under_reviewer_labels(tmp_path):
    import heldout_review

    heldout_review.make(tmp_path)
    _fill(
        tmp_path / "review_claimcheck_v2.csv",
        tmp_path / "review_claimcheck_v2.csv",
        "your_verdict",
        {"CE001": "pass", "CE002": ""},
        "ok",
    )
    before = (REPO / "evals" / "datasets" / "claimcheck_v2.json").read_bytes()
    text = heldout_review.apply("Tester", review_dir=tmp_path, verdict_dir=tmp_path / "v", report=tmp_path / "r.md")
    assert (REPO / "evals" / "datasets" / "claimcheck_v2.json").read_bytes() == before  # never edited
    assert "Reviewed 54/55; agreed with 53" in text
    assert "On reviewed labels: blocked 25/25, wrongly blocked 3/30" in text  # CE001 relabelled pass
    assert "Not reviewed yet (draft label kept): CE002" in text
    assert "Reviewed 0/36; agreed with 0" in text  # eval sheet generated but not filled: nothing counted


def test_prompt_masks_contact_and_location_but_not_the_opening_words():
    from resumeiq_api.rewrite import build_prompt

    prompt = build_prompt(
        "Deploy models to Azure",
        [EvidenceLine("E1", "Deployed Azure Container Apps in Calgary, AB; contact sam@example.com.")],
    )
    assert "Deployed Azure Container Apps" in prompt
    assert "Calgary, AB" not in prompt and "sam@example.com" not in prompt

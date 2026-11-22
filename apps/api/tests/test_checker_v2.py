"""Checker v2: requirement echo, negation, spelling variants, rebuilding verbs, placeholder outcomes."""

import pytest
from fastapi.testclient import TestClient

from resumeiq_api.app import app
from resumeiq_api.rewrite import DailyBudget, EvidenceLine, approval_token, check_claim, requirement_echo, rewrite

client = TestClient(app)


def check(draft, evidence, requirement=None):
    return check_claim(draft, [EvidenceLine("E1", evidence)], requirement)


def test_wording_copied_from_the_requirement_is_blocked():
    result = check(
        "Participated in code reviews, supporting mentorship of junior engineers.",
        "Participated in code reviews for the recommendation service.",
        "Mentor junior engineers and lead code reviews",
    )
    assert not result.passed
    assert any("job posting" in i and "mentorship" in i for i in result.issues)


def test_requirement_words_that_are_in_the_evidence_pass():
    assert check(
        "Built a fraud detection model with gradient boosting.",
        "Built a fraud detection model with gradient boosting for card payments.",
        "Build fraud detection models",
    ).passed


def test_generic_shared_words_and_short_word_matches_pass():
    assert (
        requirement_echo(
            "Built a demand model with the planning group.",
            "Work with data teams to build models",
            "Built a demand model.",
        )
        == []
    )
    # "apis" is present in "FastAPI"
    assert (
        requirement_echo(
            "Implemented endpoints for model serving APIs.",
            "Architect APIs for model serving",
            "Implemented two endpoints in the FastAPI model service.",
        )
        == []
    )


def test_without_a_requirement_the_echo_rule_is_off():
    assert check("Shaped the analytics roadmap.", "Shaped the analytics roadmap.").passed
    assert requirement_echo("anything", "", "anything") == []


@pytest.mark.parametrize(
    "draft",
    [
        "Built a nightly batch scoring job rather than a real-time stream.",
        "Built a prototype model that was not deployed to production.",
        "Wrote the validation step, not the end-to-end pipeline.",
    ],
)
def test_denied_scope_is_not_a_claim(draft):
    evidence = "Built a nightly batch scoring job; wrote the validation step of a prototype model."
    assert check(draft, evidence).passed, check(draft, evidence).issues


@pytest.mark.parametrize("draft", ["Built a scoring job that runs in real time.", "Owned the pipeline end to end."])
def test_scope_words_without_hyphens_are_caught(draft):
    result = check(draft, "Built a scoring job; wrote one step of the pipeline.")
    assert any("Wider scope" in i for i in result.issues)


def test_rebuilding_verbs_have_a_level():
    assert not check("Refactored the deployment scripts.", "Helped refactor the deployment scripts.").passed
    assert check(
        "Contributed to rebuilding the invoicing service as one of three engineers.",
        "Was one of three engineers who rebuilt the invoicing service.",
    ).passed
    assert check(
        "Rebuilt the invoicing service as one of three engineers.",
        "Was one of three engineers who rebuilt the invoicing service.",
    ).passed


def test_a_placeholder_does_not_hide_an_invented_outcome():
    evidence = "Moved two nightly jobs to smaller virtual machines."
    assert not check(
        "Moved two nightly jobs to smaller machines, reducing cloud costs by [add measurable result].", evidence
    ).passed
    assert check("Moved two nightly jobs to smaller machines, reducing [cost type] by [amount].", evidence).passed
    assert check("Moved two nightly jobs to smaller machines, [add measurable result].", evidence).passed


def test_check_endpoint_uses_the_requirement_and_stays_backward_compatible():
    body = {
        "text": "Grouped survey responses by region for customer segmentation.",
        "evidence": [{"id": "E1", "text": "Grouped survey responses by region in Excel."}],
    }
    assert client.post("/v1/rewrite/check", json=body).json()["passed"] is True  # old callers: no requirement
    with_req = client.post(
        "/v1/rewrite/check", json={**body, "requirement": "Experience with customer segmentation"}
    ).json()
    assert with_req["passed"] is False and "segmentation" in with_req["issues"][0]


def test_approval_token_binds_the_requirement():
    lines = [EvidenceLine("E1", "Built a churn model.")]
    assert approval_token("Built a churn model.", lines) != approval_token(
        "Built a churn model.", lines, "Build churn models"
    )


def test_model_drafts_are_checked_against_the_requirement_and_retried():
    answers = iter(
        [
            '{"bullet": "Grouped survey responses by region for customer segmentation."}',
            '{"bullet": "Grouped survey responses by region in Excel, [add measurable result]."}',
        ]
    )
    trace: list[dict] = []
    result = rewrite(
        "Experience with customer segmentation",
        [EvidenceLine("E1", "Grouped survey responses by region in Excel.")],
        lambda system, user: next(answers),
        DailyBudget(5),
        trace=trace,
    )
    assert result.source == "model" and result.attempts == 2
    assert not trace[0]["passed"] and "segmentation" in trace[0]["issues"][0]

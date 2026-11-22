import pytest

from resumeiq_api.rewrite import (
    DailyBudget,
    EvidenceLine,
    approval_token,
    build_prompt,
    check_claim,
    rewrite,
    rule_based_shape,
)

CONTRIB = EvidenceLine(
    "RES-E03",
    "Contributed to the deployment of the forecasting service to Azure Container Apps with the platform team.",
)
BUILT = EvidenceLine(
    "RES-E01",
    "Developed a demand-forecasting model in Python with scikit-learn that predicts weekly produce orders for 14 stores.",
)


def test_blocks_an_upgraded_claim():
    result = check_claim("Led the deployment of the forecasting service to Azure Container Apps.", [CONTRIB])
    assert not result.passed
    assert "ownership" in result.issues[0]
    assert result.token is None


def test_cannot_borrow_strength_from_a_different_line():
    borrowed = check_claim("Built the deployment of the forecasting service to Azure Container Apps.", [CONTRIB, BUILT])
    assert not borrowed.passed
    honest = check_claim("Contributed to deploying the forecasting service to Azure Container Apps.", [CONTRIB, BUILT])
    assert honest.passed


def test_blocks_invented_numbers_and_tools_but_allows_placeholders_and_source_numbers():
    bad = check_claim(
        "Developed a forecasting model in Python and PyTorch for 14 stores, cutting waste by 30%.", [BUILT]
    )
    assert not bad.passed
    assert any("30%" in i for i in bad.issues)
    assert any("pytorch" in i for i in bad.issues)
    good = check_claim("Developed a Python forecasting model for 14 stores, [add measurable result].", [BUILT])
    assert good.passed and good.token


def test_approval_is_bound_to_exact_text():
    text = "Developed a Python forecasting model for 14 stores, [add measurable result]."
    token = check_claim(text, [BUILT]).token
    assert token == approval_token(text, [BUILT])
    assert token != approval_token(text + " ", [BUILT])


def test_rule_based_shape_never_upgrades_and_uses_the_most_relevant_line():
    shape = rule_based_shape([CONTRIB, BUILT])
    assert shape.startswith("[Your verb] the deployment")
    assert check_claim(shape, [CONTRIB]).passed


def test_model_draft_is_checked_and_retried_once():
    calls = []

    def fake_model(system: str, user: str) -> str:
        calls.append(user)
        if len(calls) == 1:
            return '{"bullet": "Led the Azure deployment of the forecasting service, cutting costs by 40%."}'
        return '{"bullet": "Contributed to deploying the forecasting service to Azure Container Apps, [add measurable result]"}'

    result = rewrite("Lead cloud deployments", [CONTRIB], fake_model, DailyBudget(10))
    assert result.source == "model" and result.attempts == 2 and result.check.passed
    assert "rejected" in calls[1]


def test_falls_back_to_rules_when_the_model_keeps_failing_or_budget_is_spent():
    def stubborn(system: str, user: str) -> str:
        return '{"bullet": "Led everything with Kubernetes."}'

    assert rewrite("Lead cloud deployments", [CONTRIB], stubborn, DailyBudget(10)).source == "rules"
    spent = DailyBudget(0)
    assert rewrite("Lead cloud deployments", [CONTRIB], stubborn, spent).source == "rules"
    assert rewrite("Lead cloud deployments", [CONTRIB], None, DailyBudget(5)).source == "rules"


def test_budget_counts_down():
    budget = DailyBudget(2)
    assert budget.take() and budget.take() and not budget.take()
    assert budget.remaining() == 0


def test_prompt_masks_contact_details_and_fences_untrusted_text():
    prompt = build_prompt("Python", [EvidenceLine("E1", "Email me at jo@example.com about Python work.")])
    assert "jo@example.com" not in prompt and "[email hidden]" in prompt
    assert '<evidence id="E1">' in prompt


@pytest.mark.parametrize("text", ["", "   "])
def test_empty_bullet_fails(text):
    assert not check_claim(text, [BUILT]).passed

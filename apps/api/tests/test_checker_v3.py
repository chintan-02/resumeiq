from resumeiq_api.rewrite import EvidenceLine, canonical, check_claim, justified


def check(draft: str, evidence: str, requirement: str):
    return check_claim(draft, [EvidenceLine("E1", evidence)], requirement)


def test_language_model_phrases_are_one_word():
    assert canonical("Fine-tuned a large language model") == "Fine-tuned a llm"
    assert canonical("LLMs and language models") == "llm and llm"


def test_synonyms_are_directed():
    assert justified("stakeholders", ["store", "managers"])
    assert not justified("executives", ["store", "managers"])  # no entry: executives must be in the evidence
    assert justified("findings", ["churn", "analysis"])


def test_honest_synonyms_from_live_drafting_pass():
    assert check(
        "Presented churn analysis findings to the product lead.",
        "Presented the churn analysis to the product lead.",
        "Present findings to stakeholders",
    ).passed
    assert check(
        "Fine-tuned an open-source LLM on support tickets.",
        "Fine-tuned an open-source language model on support tickets.",
        "Fine-tune LLMs",
    ).passed
    assert check(
        "Wrote SQL views transforming order tables for the finance dashboard.",
        "Wrote SQL views over order tables for the finance dashboard.",
        "Transform raw data",
    ).passed


def test_a_synonym_never_lifts_a_claim():
    result = check(
        "Presented churn analysis findings to executive leadership.",
        "Presented the churn analysis to my team lead.",
        "Present findings to executive leadership",
    )
    assert not result.passed
    assert any("executive" in issue for issue in result.issues)
    assert not check(
        "Trained a language model to summarise tickets.",
        "Called a hosted language model API to summarise tickets.",
        "Train LLMs",
    ).passed  # same words, stronger verb: the level rule still blocks


def test_unrelated_echo_is_still_blocked():
    assert not check(
        "Reviewed pull requests, mentoring junior engineers.",
        "Reviewed pull requests for the billing service.",
        "Mentor junior engineers",
    ).passed


def test_flagged_tools_are_named_as_the_user_wrote_them():
    result = check("Deployed the scorer to Kubernetes.", "Deployed the scorer to Azure.", "Deploy services")
    assert "Tools not in your evidence: Kubernetes." in result.issues

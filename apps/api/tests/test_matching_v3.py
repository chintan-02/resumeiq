from resumeiq_api.levels import evidence_level
from resumeiq_api.matching import Thresholds, build_matcher
from resumeiq_api.matching_v2 import named_terms
from resumeiq_api.models import Coverage, EvidenceItem, Level, Requirement

TH = Thresholds(low=0.3, high=0.35)


def item(i: int, text: str) -> EvidenceItem:
    return EvidenceItem(id=f"E{i}", document_id="D1", start=0, end=len(text), text=text, level=evidence_level(text))


def req(text: str, level: Level = Level.BUILT) -> Requirement:
    return Requirement(id="R1", text=text, priority="must", required_level=level)


def test_named_terms_are_capitalised_tools_not_acronym_expansions():
    assert named_terms("Write SQL in Snowflake or BigQuery") == {"sql", "snowflake", "bigquery"}
    assert named_terms("Lead migrations of ML workloads") == set()  # ML expands to two words
    assert named_terms("Experience with A/B test analysis") == set()
    assert "build" not in named_terms("Build dashboards in Looker")  # first word is not a name


def test_listed_tool_is_not_lifted_by_a_strong_line_about_other_work():
    requirement = req("Build dashboards in Looker for business teams")
    evidence = [
        item(1, "Skills: Looker, Tableau, Excel."),
        item(2, "Built weekly dashboards in Excel for business teams."),
    ]
    v2 = build_matcher("keyword-rules-v2", TH).match(requirement, evidence)
    v3 = build_matcher("keyword-rules-v3", TH).match(requirement, evidence)
    assert v2.status is Coverage.SUPPORTED  # the bug: Looker borrows the level of the Excel line
    assert v3.status is not Coverage.SUPPORTED
    assert "looker" in v3.reason.lower()


def test_tool_used_in_its_own_line_is_still_supported():
    requirement = req("Build dashboards in Looker for business teams")
    evidence = [item(1, "Built Looker dashboards that the operations team uses each week.")]
    assert build_matcher("keyword-rules-v3", TH).match(requirement, evidence).status is Coverage.SUPPORTED


def test_generic_words_keep_the_strongest_line_rule():
    requirement = req("Automate recurring data pipelines")
    evidence = [
        item(1, "Scheduled a Python script with cron to pull and clean the daily sales export pipelines."),
        item(2, "Updated test data in the staging database."),
    ]
    v2 = build_matcher("keyword-rules-v2", TH).match(requirement, evidence)
    v3 = build_matcher("keyword-rules-v3", TH).match(requirement, evidence)
    assert v3.status is v2.status

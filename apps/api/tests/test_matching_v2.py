from resumeiq_api.matching import Thresholds, build_matcher
from resumeiq_api.matching_v2 import read_requirement
from resumeiq_api.models import EvidenceItem, Level, Requirement


def units(text: str) -> list[set[str]]:
    return [set(u) for u in read_requirement(text)[1]]


def test_slash_and_parenthesised_lists_are_alternatives():
    assert {"fastapi", "flask"} <= next(u for u in units("Build backend services with FastAPI/Flask") if "flask" in u)
    cloud = units("Deploy services to a major cloud platform (GCP, AWS, or Azure)")
    assert any({"gcp", "aws", "azure"} <= u for u in cloud)


def test_one_name_slashes_stay_whole():
    assert any("cicd" in u for u in units("Own the CI/CD pipeline"))
    assert not any("cd" in u for u in units("Own the CI/CD pipeline"))


def test_descriptors_are_not_components_and_and_lists_stay_separate():
    found = units(
        "Strong fundamentals in Python and TypeScript, with CRUD applications using frameworks such as FastAPI/Flask and React"
    )
    flat = set().union(*found)
    assert "fundamental" not in flat and "framework" not in flat
    assert any("react" in u and "flask" not in u for u in found)


def test_machine_learning_counts_once():
    found = units("Build and deploy machine learning models as REST APIs")
    assert sum("machine" in u for u in found) == 1


def test_paraphrased_audience_is_matched():
    req = Requirement(
        id="R1", text="Explain model results to non-technical stakeholders", priority="must", required_level=Level.USED
    )
    item = EvidenceItem(
        id="E1",
        document_id="E1",
        start=0,
        end=1,
        text="Presented forecast accuracy to store managers in plain language.",
        level=Level.USED,
    )
    v1 = build_matcher("keyword-rules", Thresholds(0.3, 0.35)).match(req, [item])
    v2 = build_matcher("keyword-rules-v2", Thresholds(0.3, 0.35)).match(req, [item])
    assert v1.status.value == "not_found"
    assert v2.status.value != "not_found"
    assert v2.citations[0].quote == item.text

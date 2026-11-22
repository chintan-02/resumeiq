import pytest

from resumeiq_api.evidence import segment
from resumeiq_api.levels import evidence_level, required_level
from resumeiq_api.models import Level, SourceDocument
from resumeiq_api.samples import load_samples
from resumeiq_api.terms import content_terms, term_units


def test_every_evidence_item_is_an_exact_slice_of_its_document():
    for sample in load_samples().values():
        for document in sample.documents:
            items = segment(document)
            assert items, f"no evidence found in {document.id}"
            for item in items:
                assert document.text[item.start : item.end] == item.text


def test_segmentation_skips_headings_and_splits_sentences():
    text = "# Name\n\n## Experience\n\n- Built an API in Go. Wrote the tests for it too.\nSkills:\n"
    items = segment(SourceDocument(id="D", kind="resume", title="t", text=text))
    assert [i.text for i in items] == ["Built an API in Go.", "Wrote the tests for it too."]


@pytest.mark.parametrize(
    ("text", "level"),
    [
        ("Contributed to the team's deployment of the service to Google Cloud Run.", Level.USED),
        ("Led the deployment of the service to Google Cloud Run.", Level.OWNED),
        ("Built and deployed a FastAPI service that serves a model.", Level.BUILT),
        ("Completed an online course covering Kubernetes basics.", Level.AWARE),
        ("Read about Docker and containerization while preparing for interviews.", Level.AWARE),
        ("Helped prepare the weekly KPI report that the manager presented.", Level.USED),
        ("Python, scikit-learn, pandas, SQL", Level.AWARE),
    ],
)
def test_evidence_level_follows_the_labelling_guide(text, level):
    assert evidence_level(text) == level


def test_required_level_matches_every_labelled_requirement(dataset_path):
    import json

    data = json.loads(dataset_path.read_text(encoding="utf-8"))
    mismatches = [
        (r["text"], r["required_level"], int(required_level(r["text"])))
        for job in data["jobs"].values()
        for r in job["requirements"]
        if int(required_level(r["text"])) != r["required_level"]
    ]
    assert mismatches == []


def test_tool_names_are_not_mangled_by_the_stemmer():
    assert "docker" in content_terms("Hands-on experience with Docker")
    assert "docker" in content_terms("Wrote a Dockerfile for the API")


def test_alternatives_count_as_one_unit():
    text = "Lead the deployment of models to a cloud platform such as GCP or AWS"
    units = term_units(text, content_terms(text))
    assert frozenset({"gcp", "aws"}) in units

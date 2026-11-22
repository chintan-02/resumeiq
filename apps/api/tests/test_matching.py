from resumeiq_api.evidence import segment
from resumeiq_api.fitmap import tuned_matcher
from resumeiq_api.models import Coverage, Level, Requirement, SourceDocument

LEAD = Requirement(
    id="R1",
    text="Lead the deployment of models to a cloud platform such as GCP or AWS",
    required_level=Level.OWNED,
)


def _evidence(text: str):
    return segment(SourceDocument(id="D", kind="resume", title="t", text=text))


def test_contributed_is_not_led():
    """The demo-video case: the same nouns, a weaker claim."""
    matcher = tuned_matcher("keyword-rules")
    contributed = matcher.match(
        LEAD, _evidence("- Contributed to the deployment of models to GCP with the platform team.")
    )
    led = matcher.match(LEAD, _evidence("- Led the deployment of models to GCP across three teams."))
    assert contributed.status is Coverage.PARTIAL
    assert "ownership" in contributed.reason
    assert led.status is Coverage.SUPPORTED


def test_naive_keyword_matcher_cannot_tell_the_difference():
    """Why the rule-aware matcher exists: plain word overlap rates both the same."""
    matcher = tuned_matcher("keyword")
    contributed = matcher.match(
        LEAD, _evidence("- Contributed to the deployment of models to GCP with the platform team.")
    )
    led = matcher.match(LEAD, _evidence("- Led the deployment of models to GCP across three teams."))
    assert contributed.status == led.status


def test_citations_point_to_exact_source_text():
    text = "# CV\n\n- Built a Go REST API with PostgreSQL.\n- Wrote integration tests for it.\n"
    document = SourceDocument(id="D", kind="resume", title="t", text=text)
    result = tuned_matcher("keyword-rules").match(
        Requirement(id="R1", text="Design and build REST APIs with Python or Go", required_level=Level.BUILT),
        segment(document),
    )
    assert result.status is Coverage.SUPPORTED
    for citation in result.citations:
        assert document.text[citation.start : citation.end] == citation.quote


def test_not_found_has_no_citations():
    result = tuned_matcher("keyword-rules").match(
        Requirement(id="R1", text="Experience with Airflow", required_level=Level.USED),
        _evidence("- Built a Go REST API with PostgreSQL."),
    )
    assert result.status is Coverage.NOT_FOUND
    assert result.citations == []


def test_numbers_alone_are_not_key_terms():
    from resumeiq_api.terms import content_terms

    assert "3+" not in content_terms("3+ years of Python")
    assert {"python", "c++", "s3"} <= content_terms("Python, C++ and S3")

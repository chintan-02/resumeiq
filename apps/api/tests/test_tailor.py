from resumeiq_api.fitmap import build_fit_map
from resumeiq_api.health import check_resume
from resumeiq_api.models import ActionKind, SourceDocument
from resumeiq_api.privacy import privacy_mode
from resumeiq_api.tailor import wording_mismatches

RESUME = """Sam Rivera
Calgary, AB · sam@example.com

EXPERIENCE
Data Analyst, Northfield Utilities (fictional) · 2023–2026
- Built a FastAPI service that serves a churn model to the billing team every night.
- Wrote SQL in Postgres to assemble weekly training tables for three product lines.
- Contributed to the deployment of the scoring service to AWS with the platform team.
- Responsible for weekly reporting.

EDUCATION
- Completed a course on Kubernetes fundamentals.

SKILLS
Python, Airflow, Tableau, Docker, Git
"""

JOB = """Requirements
- Write SQL against PostgreSQL to build training datasets
- Lead deployments to a cloud platform such as AWS or GCP
- Hands-on experience with Kubernetes in production
- Experience with Airflow
- Build dashboards in Tableau or Looker for business stakeholders
- Experience with Terraform
Nice to have
- Experience with Spark
"""


def fit():
    doc = SourceDocument(id="RES", kind="resume", title="Resume", text=RESUME)
    return build_fit_map([doc], "Test job", job_text=JOB), doc


def kinds_for(fit_map, text_part):
    req = next(r for r in fit_map.results if text_part in r.requirement.text)
    return {a.kind for a in fit_map.actions if a.requirement_id == req.requirement.id}


def test_every_action_kind_comes_from_the_evidence():
    fit_map, doc = fit()
    assert ActionKind.BELOW_LEVEL in kinds_for(fit_map, "Lead deployments")
    assert ActionKind.LEARNED_NOT_USED in kinds_for(fit_map, "Kubernetes")
    assert ActionKind.LISTED_NOT_SHOWN in kinds_for(fit_map, "Airflow")
    assert ActionKind.MISSING in kinds_for(fit_map, "Terraform")
    assert ActionKind.MISSING in kinds_for(fit_map, "Spark")
    assert any(a.kind is ActionKind.WORDING and a.terms == ["PostgreSQL", "Postgres"] for a in fit_map.actions)


def test_actions_are_ordered_and_cite_exact_text():
    fit_map, doc = fit()
    priorities = [a.priority for a in fit_map.actions]
    assert priorities == sorted(priorities)
    assert [a.id for a in fit_map.actions] == [f"A{i + 1:02d}" for i in range(len(fit_map.actions))]
    for action in fit_map.actions:
        for c in action.citations:
            assert doc.text[c.start : c.end] == c.quote


def test_no_action_ever_suggests_a_stronger_claim_or_a_number():
    fit_map, _ = fit()
    for action in fit_map.actions:
        if action.suggestion:
            assert not any(w in action.suggestion.lower().split() for w in ("led", "owned", "managed"))
            assert "[add measurable result]" in action.suggestion
        assert "hire" not in action.detail.lower() and "reject" not in action.detail.lower()


def test_skills_list_is_never_asked_for_a_result():
    fit_map, _ = fit()
    for action in fit_map.actions:
        if action.kind is ActionKind.ADD_RESULT:
            assert "Python, Airflow" not in action.citations[0].quote


def test_nice_to_have_gaps_rank_below_must_haves():
    fit_map, _ = fit()
    spark = next(a for a in fit_map.actions if "Spark" in a.title)
    terraform = next(a for a in fit_map.actions if "Terraform" in a.title)
    assert terraform.priority == 1 and spark.priority == 3


def test_wording_ignores_lowercase_lookalikes():
    assert wording_mismatches("We use ML daily", "Built an html page") == []
    assert wording_mismatches("Experience with Kubernetes", "Ran workloads on K8s") == [("Kubernetes", "K8s")]


def test_health_checklist_has_no_score_and_flags_real_issues():
    _, doc = fit()
    checks = {c.id: c for c in check_resume(doc)}
    assert checks["sections"].status == "pass"
    assert checks["weak_openings"].status == "warn" and len(checks["weak_openings"].items) == 2
    assert checks["results"].status == "warn"
    assert all(c.status in ("pass", "warn") for c in checks.values())


def test_health_catches_template_text_and_generic_phrases():
    doc = SourceDocument(
        id="RES", kind="resume", title="Resume", text="Your Name\nResults-driven team player.\nCompany Name"
    )
    checks = {c.id: c for c in check_resume(doc)}
    assert checks["placeholders"].status == "warn"
    assert {"results-driven", "team player"} <= set(checks["generic"].items)
    assert checks["contact"].status == "warn"


def test_privacy_mode_hides_name_location_and_contact():
    masked = privacy_mode(RESUME)
    assert "Sam Rivera" not in masked and "Calgary, AB" not in masked and "sam@example.com" not in masked
    assert "EXPERIENCE" in masked and "Northfield Utilities" in masked


def test_privacy_mode_leaves_a_heading_on_the_first_line():
    assert privacy_mode("Professional Experience\n- Built a model.").startswith("Professional Experience")

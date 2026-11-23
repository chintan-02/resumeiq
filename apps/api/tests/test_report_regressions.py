"""Synthetic reproductions of misleading matches found during a fit-map review."""

from fastapi.testclient import TestClient

from resumeiq_api.app import app
from resumeiq_api.fitmap import build_fit_map
from resumeiq_api.models import ActionKind, Coverage, SourceDocument

RESUME = SourceDocument(
    id="RES",
    kind="resume",
    title="Synthetic resume",
    text="""APPLIED AI ENGINEER • PYTHON • FASTAPI
- Built a Python FastAPI app with a Gemini agent and Google ADK tool calling.
  Passed 25/25 scripted turns after deploying it to Cloud Run.
- Built a policy RAG system with embeddings and ChromaDB vector retrieval.
  Passed 23/24 cases, including four evidence-gated refusals.
- Built an application that traces regulatory changes to controls for analysts.
- Wrote unit tests with pytest and configured GitHub Actions CI/CD.
- Developed client web applications end-to-end with Git.
""",
)


def test_named_tools_and_duration_need_direct_evidence():
    jd = """Requirements
- Implement LLM tracing, monitoring, and evaluation using Langfuse
- Understanding of Model Context Protocol (MCP) and its use in connecting AI agents
- 2+ years of experience developing agentic AI or LLM-powered applications
- Mentor developers and provide guidance through design and code reviews
- Experience with Google Cloud services such as Vertex AI and BigQuery
- Desirable Skills and Experience
- Familiarity with LangGraph
"""
    fit = build_fit_map([RESUME], "Synthetic role", job_text=jd)
    assert len(fit.results) == 6
    assert fit.results[-1].requirement.priority == "nice"
    for result, expected in zip(
        fit.results, ["Langfuse", "MCP", "2+ years", "mentoring", "Vertex AI", "LangGraph"], strict=True
    ):
        assert result.status is not Coverage.SUPPORTED
        assert any(expected in note for note in result.verification_notes)
        actions = [a for a in fit.actions if a.requirement_id == result.requirement.id]
        assert len(actions) == 1
        assert actions[0].suggestion is None


def test_real_evidence_and_metrics_survive_bullet_wrapping():
    jd = """Requirements
- Deploy AI services on Google Cloud
- Experience building RAG solutions using embeddings and vector search
- Experience with automated testing, Git, and CI/CD practices
- Experience building RAG solutions using embeddings and vector search.
"""
    fit = build_fit_map([RESUME], "Synthetic role", job_text=jd)
    assert len(fit.results) == 3
    deployment, rag, ci = fit.results
    assert all(result.status is not Coverage.NOT_FOUND for result in (deployment, rag, ci))
    assert any("23/24" in citation.quote for citation in rag.citations)
    for result in fit.results:
        for citation in result.citations:
            assert RESUME.text[citation.start : citation.end] == citation.quote
    assert not any(a.kind is ActionKind.ADD_RESULT and a.requirement_id == rag.requirement.id for a in fit.actions)


def test_claim_check_pass_does_not_approve_an_unfinished_draft():
    line = "Built a Python app to process invoices"
    response = TestClient(app).post(
        "/v1/rewrite/check",
        json={"text": f"{line}, [add measurable result]", "evidence": [{"id": "E1", "text": line}]},
    )
    assert response.status_code == 200
    assert response.json()["passed"]
    assert response.json()["approval_token"] is None

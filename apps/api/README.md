# resumeiq-api (v2)

Evidence-grounded requirement matching, resume uploads and checked bullet drafting for ResumeIQ v2. Milestone
notes: [`docs/v2/`](../../docs/v2/).

```bash
pip install -e ".[dev]"
pytest -q
uvicorn resumeiq_api.app:app --reload
```

| Module | Responsibility |
| --- | --- |
| `evidence.py` | Split documents into sentences and bullets; every item keeps exact character offsets |
| `levels.py` | Rule-based strength levels (aware, used, built, owned) for evidence and requirements |
| `requirements.py` | Extract requirements from an untrusted job description; drop instruction-like lines |
| `terms.py` | Normalisation, synonyms, light stemming, "X or Y" alternatives |
| `matching.py` | `keyword`, `keyword-rules`, `embedding`, `embedding-rules` matchers |
| `matching_v2.py` | `keyword-rules-v2` (default): alternatives, descriptors and concept groups in requirements |
| `fitmap.py` | Assemble the fit map; only confirmed evidence is used |
| `evaluation.py` | Metrics, dev-only threshold tuning, bootstrap confidence intervals |
| `uploads.py`, `privacy.py` | Read PDF/DOCX/TXT in memory; mask email, phone and links |
| `rewrite.py` | Draft a bullet (optional Claude call behind a daily budget), `check_claim`, approval tokens |
| `app.py` | FastAPI: `/health`, `/v1/samples…`, `POST /v1/fit-map`, `POST /v1/fit-map/upload`, `POST /v1/rewrite`, `POST /v1/rewrite/check`, `GET /v1/rewrite/status` |

`tuned_thresholds.json` is written by `python evals/run_baseline.py` and `python evals/run_eval_v1.py`. Do not edit
it by hand.

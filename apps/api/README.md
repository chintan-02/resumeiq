# resumeiq-api (v2)

Evidence-grounded requirement matching for ResumeIQ v2. Milestone 1 scope and decisions:
[`docs/v2/MILESTONE_1.md`](../../docs/v2/MILESTONE_1.md).

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
| `fitmap.py` | Assemble the fit map; only confirmed evidence is used |
| `evaluation.py` | Metrics, dev-only threshold tuning, bootstrap confidence intervals |
| `app.py` | FastAPI: `/v1/samples`, `/v1/samples/{id}/fit-map` (precomputed), `POST /v1/fit-map` |

`tuned_thresholds.json` is written by `python evals/run_baseline.py`. Do not edit it by hand.

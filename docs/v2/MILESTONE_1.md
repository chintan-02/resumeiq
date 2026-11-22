# ResumeIQ v2 · Milestone 1: working fit map + baseline report

**Finish line:** a working fit map with exact source quotes, and a baseline report anyone can reproduce
with one command. No LLM calls in this milestone.

## What is in this milestone

| Piece | Where | What it does |
| --- | --- | --- |
| Labelling guide | `evals/LABELING_GUIDE.md` | Defines evidence levels (aware, used, built, owned) and the supported / partial / not_found rules |
| Eval set | `evals/datasets/eval_v0.json` | 54 synthetic cases, 6 candidates, 4 job families, disjoint dev/test splits, keyword-trap cases |
| Walkthrough sample | `apps/api/src/resumeiq_api/samples/walkthrough/` | One synthetic resume, one project write-up, one job description. **Never evaluated** |
| Fit-map API | `apps/api/src/resumeiq_api/` | Segments documents with exact offsets, extracts requirements, matches them, returns quotes |
| Baseline report | `evals/reports/baseline_v0/REPORT.md` | Keyword vs keyword + strength rules; embeddings run locally |

## Decisions made explicit before coding

1. **Walkthrough ≠ evaluation.** The demo sample proves the workflow end to end. Quality numbers come only from
   the separate labelled set, which includes cases where the right keyword appears but the evidence supports a
   weaker claim. A test fails if demo evidence ever appears in the eval set.
2. **The public demo works without live inference.** It is described as *"sample resumes with optional custom job
   descriptions"*. A precomputed walkthrough is served from `GET /v1/samples/walkthrough/fit-map`, and CI fails if
   it drifts from the live result. Custom job descriptions are capped (12,000 characters, 30 requirements) and
   treated as untrusted: instruction-like lines are dropped and reported, and tests confirm they cannot change
   the response shape, the statuses or the citations. When an LLM step is added, the backend must check a global
   spend budget **before** any provider call; per-IP limits and Turnstile are additional, not the main control.
3. **Approval is tied to exact text** (applies from the tailor step onward): editing an approved bullet, or a change
   to its cited evidence, invalidates approval; export requires the current version to pass verification and be
   approved again. The demo video shows "contributed to deployment" rewritten as "led the deployment" and blocked
   (see `tests/test_matching.py::test_contributed_is_not_led`).

## Run it

```bash
pip install -e "apps/api[dev]"
cd apps/api && pytest -q && cd ../..
python evals/run_baseline.py --check          # reproduces the committed report exactly
uvicorn resumeiq_api.app:app --reload          # then open http://127.0.0.1:8000/docs
```

Embedding comparison (needs a model download, so it runs on your machine):

```bash
pip install -e "apps/api[embeddings]"
python evals/run_baseline.py --matchers keyword keyword-rules embedding embedding-rules
```

## Open items before the live release

- [ ] Human review of all 54 draft labels; a second reviewer on the `ambiguous` and `trap` cases
- [ ] Run and commit the embedding comparison
- [ ] Build eval_v1 with a fresh test split before changing the matcher in response to eval_v0 test errors
- [ ] Next.js demo: parse preview, fit map, grounded bullet review, DOCX export

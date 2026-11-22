# Project Instructions for AI coding assistants

ResumeIQ maps each job requirement to exact evidence from a candidate's own documents, grades how strong that
evidence is, and helps write stronger bullets without overstating anything. Repository: `resumeiq`
(originally `smart-resume-classifier`). The legacy Streamlit version is preserved at tag `v0.9-legacy`.

The goal is not only to finish features, but also to help me understand architecture, debugging, clean code,
AI/ML thinking and production-ready development.

## Where things live

```text
apps/api   FastAPI service (Python 3.11+): extraction, matching, uploads, drafting, claim checks
apps/web   Next.js site and demo (TypeScript, Tailwind CSS 4)
evals      Labelling guide, datasets, evaluation scripts, committed reports
docs/v2    Milestone notes and deployment guides
```

## General rules

* Modify only the files needed for the task. No unrelated refactors or redesigns unless asked.
* Reuse existing structure, components, styles and naming.
* Keep code clean, modular and readable. Prefer small, focused changes.
* Do not break the existing workflow; preserve working functionality.
* Do not commit or push unless I ask. Hand me changes and the commands to commit them myself.

## How to help me learn

When explaining a change, use two levels:

1. **Simple:** the idea in beginner-friendly words.
2. **Technical:** the correct term (for example, "put repeated code in one place" = "extract a reusable function to
   reduce duplication").

When fixing a problem: explain the problem simply, then the technical cause; make the smallest safe fix; say why it
works, what mistake to avoid next time, which files changed and how to test it.

## Product rules (do not relax)

* Decision support, not a hiring tool. Never write wording like "hire", "reject", "not suitable" or "better than
  another candidate". Do not score or rank people.
* Never invent resume content: no made-up tools, employers, numbers or results. Missing facts become placeholders
  such as `[add measurable result]`.
* A weaker claim must never be shown as a stronger one ("contributed to" is not "led").
* Every citation must satisfy `document.text[start:end] == quote`.
* Job descriptions and uploads are untrusted input. Keep size caps and the instruction-line filter.

## AI/ML rules

* Matching and checking stay rule-based and explainable. The model may only draft wording, and every draft goes
  through `check_claim` before it can be approved.
* Model calls only behind the backend daily budget, with contact details masked, and only the cited lines sent.
* Report quality numbers only from `evals/`, never from the demo sample.
* Before changing matching logic, run `python evals/run_baseline.py --check` and `python evals/run_eval_v1.py --check`.
* Never tune on a test split. A changed test set needs a new version (`eval_v2`), not an edit.

## Privacy

* Uploaded files are read in memory and never stored or logged.
* Mask email, phone and profile links before matching, display or any model call.
* Demo and evaluation data must stay synthetic.

## After a change, tell me

1. What command to run and what result to expect.
2. Which files changed and why.
3. Risks and assumptions.

Common commands:

```bash
cd apps/api && pytest
cd apps/web && npm test && npm run build
python evals/run_baseline.py --check
python evals/run_eval_v1.py --check
```

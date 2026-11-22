# ResumeIQ

**Match every job requirement to a line you actually wrote, and never claim more than that line proves.**

[![API CI](https://github.com/chintan-02/resumeiq/actions/workflows/api.yml/badge.svg)](https://github.com/chintan-02/resumeiq/actions/workflows/api.yml)
[![Web CI](https://github.com/chintan-02/resumeiq/actions/workflows/web.yml/badge.svg)](https://github.com/chintan-02/resumeiq/actions/workflows/web.yml)
[![Release](https://img.shields.io/github/v/release/chintan-02/resumeiq)](https://github.com/chintan-02/resumeiq/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

[**Live demo**](https://resumeiq-chintan.vercel.app/demo) ·
[How it works](#how-it-works) ·
[Architecture](#architecture) ·
[Evaluation](#evaluation) ·
[Engineering milestones](#engineering-milestones) ·
[Run it locally](#run-it-locally)

![ResumeIQ landing page](docs/assets/resumeiq-hero.png)

## In 30 seconds

| | |
| --- | --- |
| **What it is** | A full-stack AI web app. Paste a job posting (and optionally upload a resume), and ResumeIQ maps every requirement to the exact sentence that proves it, grades how strong that proof is, and tells you what to fix first. |
| **The hard part** | It can draft a stronger resume bullet with an LLM, but a deterministic claim checker blocks any draft that says more than your evidence: "contributed to the deployment" can never become "led the deployment". |
| **Why it is credible** | Every quality number comes from labelled held-out test sets that were frozen before the code they test, scored once, and re-checked in CI. Live model runs are audited, and the misses are published next to the wins. |
| **Stack** | Next.js 16, React 19, TypeScript, Tailwind CSS 4 on Vercel · Python 3.12, FastAPI, Pydantic on Google Cloud Run · Claude API (optional) · GitHub Actions, Secret Manager, Cloud Monitoring |
| **Scale of the work** | 148 API tests and 20 web tests · 7 labelled datasets for matching and checking, 3 live model runs · 4 tagged releases |

## Why build this

Tailoring a resume to a job has two common failure modes, and existing tools tend to make both worse:

1. **Keyword matching without proof.** Many tools give a "match score" from shared words. A resume that lists
   *Kubernetes* in a skills line scores the same as one that shows running Kubernetes in production. The score
   says nothing about *where* the proof is or *how strong* it is.
2. **AI rewriting that inflates.** Ask a language model to "make this bullet fit the job" and it will happily turn
   *helped with the migration* into *led the migration*, add a percentage, or name a tool you never used. That
   reads well until an interviewer asks about it.

Both failures hurt the candidate: the first hides real gaps, the second creates claims they cannot defend.

**ResumeIQ's position:** a resume claim is only as strong as the sentence behind it. So the product is built around
**evidence**, not scores:

- every requirement is linked to an exact quote (character offsets, verified),
- evidence strength is graded (*aware → used → built → owned*), so "asks you to lead" against "you contributed"
  is shown as a gap,
- AI is allowed to *word* things, never to *judge* them; judgment stays in explainable rules that are measured.

It is decision support for the candidate, not a hiring tool: it never scores, ranks or rejects people.

## How it works

```mermaid
flowchart LR
  A["1 · Paste a job posting<br/>(+ optional resume)"] --> B["2 · Extract requirements<br/>untrusted text, rule-based"]
  B --> C["3 · Match each requirement<br/>to exact evidence + strength"]
  C --> D["4 · Tailor plan<br/>what to fix first"]
  C --> E["5 · Draft a bullet<br/>LLM optional"]
  E --> F{"6 · Claim checker<br/>deterministic"}
  F -- passes --> G["Approve<br/>bound to exact text"]
  F -- "blocked: one retry,<br/>then rule-based fallback" --> E
```

### 1. Paste a posting, optionally upload a resume

PDF, DOCX or TXT up to 2 MB, read in memory and never stored. Contact details are masked before anything else
happens. Without an upload the demo uses a synthetic sample resume.

![Paste a job description](docs/assets/resumeiq-paste-job.png)

### 2. Requirements are extracted, and the posting is treated as untrusted input

Pay, benefits and hiring-policy lines are left out. Lines that try to instruct an AI system are dropped *and shown
to you*, so a posting cannot steer the matcher or the drafting prompt.

![A prompt-injection line in a posting is ignored and reported](docs/assets/resumeiq-injection-ignored.png)

### 3. Fit map: every requirement linked to the line that proves it

Each requirement is *backed*, *partly backed* or *no evidence found*. Click one and the quote is highlighted in the
original document. Here the job asks to **lead** a cloud deployment, the resume only shows **contributing**, so it
is partly backed and says why.

![Fit map with a partly backed requirement and highlighted evidence](docs/assets/resumeiq-demo.png)

### 4. Tailor plan: what to change for this job, most important first

Gaps on must-haves first, then polish. Every step quotes the line it is about, and every suggestion is a shape with
placeholders (`[Your verb]`, `[add measurable result]`), never invented facts.

![Tailor plan](docs/assets/resumeiq-tailor-plan.png)

### 5–6. Drafting with a claim checker in the loop

A draft (from the model, or the rule-based shape when AI is off) must pass `check_claim` before it can be approved.
Below, a user edited the bullet to claim more than the evidence shows. Every overstatement is named and
**Approve is disabled** until the text is honest. Approval is a hash of the exact text and its evidence, so any
later edit needs a fresh check.

![Claim checker blocking an overstated bullet](docs/assets/resumeiq-claim-check-blocked.png)

### Also included

| Skills by area | Resume checklist (no score, on purpose) |
| --- | --- |
| ![Skills grouped by area and coloured by evidence strength](docs/assets/resumeiq-skills.png) | ![Resume checklist](docs/assets/resumeiq-resume-check.png) |

Privacy mode hides name and location on screen, and the plan exports to Markdown or PDF without the full resume.

## Architecture

```mermaid
flowchart TB
  U[Browser] --> W["Next.js on Vercel<br/>static pages + backend-for-frontend routes"]
  W -->|"JSON / multipart<br/>size caps, rate limits"| A["FastAPI on Cloud Run<br/>max 2 instances, least-privilege account"]
  subgraph API["FastAPI service"]
    X["Upload reader<br/>PDF / DOCX / TXT, in memory"] --> P["Privacy<br/>mask email, phone, links"]
    P --> S["Segmenter<br/>sentences with exact offsets"]
    J["Requirement extractor<br/>untrusted input filter"] --> M
    S --> M["Matcher v3<br/>term units, IDF, strength rules"]
    M --> T["Tailor plan + resume checklist"]
    M -->|"cited lines only"| D
    D["Drafting<br/>daily budget, masked cited lines"] --> C["Claim checker<br/>deterministic rules"]
  end
  A --> API
  D -.->|"only if a key is set"| L["Claude API<br/>(Haiku)"]
  K[(Secret Manager)] -.-> A
  A -.-> O["Cloud Logging, Error Reporting,<br/>uptime check + alert"]
```

**Request path for a draft** (the only place a model is ever called):

```mermaid
sequenceDiagram
  participant B as Browser
  participant N as Next.js route
  participant F as FastAPI
  participant L as Claude API
  B->>N: Draft a bullet for requirement R
  N->>F: POST /v1/rewrite (rate-limited)
  F->>F: Budget left? Key set? Mask contacts
  F->>L: Requirement + 1–3 cited lines, fenced as untrusted data
  L-->>F: One bullet
  F->>F: check_claim(draft, evidence, requirement)
  alt blocked
    F->>L: One retry with the named problems
    L-->>F: New bullet
    F->>F: check_claim again, else rule-based fallback
  end
  F-->>N: Draft + issues + approval token (only if passed)
  N-->>B: Show draft, Approve enabled only if it passed
```

### Repository layout

```text
apps/api      FastAPI service: extraction, matching, uploads, drafting, claim checks (Python)
apps/web      Next.js site and demo (TypeScript)
evals         Labelling guide, frozen datasets, evaluation scripts and committed reports
docs/v2       Milestone notes, deployment and operations guides
```

### API

| Endpoint | Purpose |
| --- | --- |
| `GET /v1/samples/{id}/fit-map` | Precomputed fit map for the synthetic sample (CI fails if it drifts from the live result) |
| `POST /v1/fit-map` | Fit map for a pasted job description against the sample resume |
| `POST /v1/fit-map/upload` | Same, for an uploaded resume (read in memory, never stored) |
| `POST /v1/rewrite` | Draft a bullet: model if enabled and within budget, otherwise the rule-based shape |
| `POST /v1/rewrite/check` | Run the claim checker on any text; returns issues or an approval token |
| `GET /v1/rewrite/status` | Whether AI drafting is on, the model, and the remaining daily budget |
| `GET /health` | Liveness for Cloud Run and the uptime check |

### Stack

| Layer | Technology | Why this choice |
| --- | --- | --- |
| Web | Next.js 16 (App Router), React 19, Tailwind CSS 4 | Static pages where possible; a backend-for-frontend so the browser never calls the API directly |
| API | Python 3.12, FastAPI, Pydantic 2, pypdf, python-docx | Typed request and response models; the ML and text tooling lives in Python |
| Matching | Rule-based term units, IDF ranking, evidence-strength rules | Explainable and free per request; an embedding matcher was measured and kept only as a baseline (see below) |
| LLM | Claude Haiku via the Messages API, optional | Only drafts wording; thinking off, short replies, one retry, daily budget |
| Evaluation | Labelled synthetic sets, bootstrap and Wilson CIs, frozen by sha256 | Numbers that can be reproduced by anyone in one command |
| Infra | Vercel, Google Cloud Run, Secret Manager, Cloud Monitoring, GitHub Actions | Scales to zero, capped at 2 instances, key never in code or CI |

## Engineering decisions

| Decision | Why | Trade-off accepted |
| --- | --- | --- |
| **Rules judge, the model only words** | Every status can be traced to a quote and a rule; the demo costs nothing per visitor; behaviour is testable | Rules miss meaning that words do not show (see limits below) |
| **Citations are offsets, not copied text** | `document[start:end] == quote` is checked; the UI refuses to highlight anything that fails | More bookkeeping in segmentation |
| **The checker never trusts the model** | New numbers, tools, stronger verbs, wider scope, invented outcomes and wording copied from the posting are blocked; one retry, then a rule-based fallback | Some honest drafts are blocked (measured below) |
| **Job descriptions are untrusted** | Size caps (12,000 characters, 30 requirements); instruction-like lines dropped and reported; tests prove they cannot change statuses or citations | A real line that looks like an instruction could be dropped, so it is shown |
| **Cost capped in layers** | No key → no calls; with a key: per-instance daily budget × 2 instances, 400 output tokens, provider spend cap | Drafting stops for the day when the budget is used |
| **Privacy by construction** | Uploads never stored; contacts masked before matching, display or any model call; logs hold route, status and latency only | Harder debugging, solved with structured logs and Error Reporting with messages removed |
| **No agent framework** | The flow is draft → check → retry → fallback; LangGraph would add weight without a capability | Revisit if the flow becomes a real graph |

## Evaluation

Quality numbers come only from labelled, synthetic evaluation sets, **never from the demo sample**. The protocol is
the same for every version of the matcher and the checker:

```mermaid
flowchart LR
  A["Write a new test set<br/>aimed at the known failure"] --> B["Freeze it<br/>sha256 recorded"]
  B --> C["Score the current version<br/>(totals only)"]
  C --> D["Build the new version<br/>tune on dev sets only"]
  D --> E["Score once<br/>on the frozen set"]
  E --> F["Publish every error<br/>CI re-checks the report"]
  F --> G["That set becomes dev data<br/>for the next version"]
  G --> A
```

**Why rules, not embeddings?** On the first set, a sentence-embedding matcher alone scored macro-F1 0.36 against
0.40 for plain keywords. Adding the evidence-strength rules lifted both to 0.71. The rules carried the gain, so the
production matcher stayed rule-based and free. ([baseline report](evals/reports/baseline_v0/REPORT.md))

### Matching: requirement → evidence → status

| Matcher | Held-out set | Macro-F1 [95% CI] | Accuracy | Keyword traps correct |
| --- | --- | --- | --- | --- |
| Word overlap | `eval_v1` | 0.49 [0.31, 0.65] | 0.50 | 0/4 |
| v1: + strength rules | `eval_v1` | 0.60 [0.42, 0.75] | 0.64 | 3/4 |
| v2: + requirement reading | `eval_v1` | 0.73 [0.56, 0.88] | 0.75 | 3/4 |
| v2 | `eval_v2` (skills lists, cross-line traps) | 0.69 [0.52, 0.88] | 0.82 | 9/12 |
| **v3: + strength per named skill** (live) | `eval_v2` | **0.77 [0.55, 0.95]** | **0.85** | 9/12 |

v3 fixed a real bug: v2 judged strength from the strongest cited line, so `Skills: Looker` plus an unrelated
`Built weekly reports in Excel` could read as building Looker dashboards. v3 judges each named tool by the best line
that actually mentions it. The intervals overlap and the trap score did not move: the remaining trap misses are a
strong verb on the wrong work ("Led inventory planning" for "Lead data platform migrations"), which keyword rules
cannot read. Reports: [eval_v1](evals/reports/eval_v1/REPORT.md), [eval_v2](evals/reports/eval_v2/REPORT.md).

### Claim checker: does it block overstatement without blocking honest drafts?

| Checker | Held-out set | Overstated drafts blocked | Honest drafts wrongly blocked |
| --- | --- | --- | --- |
| v0: numbers, tools, verbs | `claimcheck_v1` | 15/34 (44%) | 1/26 |
| v1: + team credit, scope words, invented outcomes, number formats | `claimcheck_v1` | 33/34 (97%) | 0/26 |
| v1 | `claimcheck_v2` (with job requirements) | 9/26 (35%) | 6/29 |
| v2: + wording copied from the posting, negation, spelling, placeholder outcomes | `claimcheck_v2` | 26/26 | 2/29 |
| v2 | `claimcheck_v3` (honest synonyms, look-alike words) | 20/20 | 15/20 |
| **v3: + directed synonyms** ("stakeholders" from "managers", never "executives" from "team lead") | `claimcheck_v3` | **20/20** | **3/20** |

Reports: [v2](evals/reports/claimcheck_v2/REPORT.md), [v3](evals/reports/claimcheck_v3/REPORT.md).

### Live model runs: what the real model writes

Each run sends requirements that ask for more than the evidence shows through the unchanged production path
(`claude-haiku-5-5`: draft → check → one retry → rule-based fallback), then audits every final bullet.

| Run | Checker | First drafts blocked | Final bullet from the model | Final bullets that still overstate (AI audit) |
| --- | --- | --- | --- | --- |
| [`drafting_v0`](evals/reports/drafting_v0/NOTES.md) (24 cases) | v1 | 4/24 | 23/24 | 4/23 clear, 5/23 borderline |
| [`drafting_v1`](evals/reports/drafting_v1/NOTES.md) (24 cases) | v2 | 19/24 (15 real, 1 borderline, 3 false alarms) | 20/24 | 0/20 clear, 2/20 borderline |
| [`drafting_v2`](evals/reports/drafting_v2/NOTES.md) (20 cases) | v3 | 15/20 (6 real, 5 borderline, 4 false alarms) | 15/20 | 0/15 clear, 3/15 borderline |

**What the live runs taught:**

- The model rarely inflates verbs, numbers or tools. Its real habit is **echoing the job posting** into an extra
  clause ("supporting mentorship of junior engineers" from evidence about code reviews). Checker v2 was built for
  exactly that, and clear overstatements in final bullets went from 4/23 to 0.
- **Held-out numbers can be optimistic.** Checker v3 cut honest-draft false alarms from 15/20 to 3/20 on its test
  set, but live false alarms did not fall, because the model used new synonyms ("data quality check" for counting
  rows). The same author wrote that set and the synonym list. Decision: keep v3, stop growing a hand-written list,
  and move to a meaning-based check that can only *clear* an echo flag, never override the other rules.

### Honest limits

- All sets are small and synthetic, and labels were drafted by an AI assistant, so confidence intervals are wide
  and numbers are optimistic. An [AI second-pass review](evals/reports/heldout_review.md) agreed with 36/36 matching
  labels and 54/55 claim-check labels. The one disagreement is recorded as an
  [open question](evals/reports/claimcheck_v3/NOTES.md). A human review kit (`evals/review/heldout_review.py`)
  is ready and never edits a frozen set.
- Keyword rules cannot tell *which work* a strong verb applies to, and cannot see synonyms outside their list.
  Both are documented, with the next step for each.

## Engineering milestones

| Release | What shipped | Engineering focus |
| --- | --- | --- |
| [`v0.9-legacy`](https://github.com/chintan-02/resumeiq/tree/v0.9-legacy) | *Smart Resume Classifier*: Streamlit app with a role classifier, ATS-style scores and batch ranking | Starting point; scores and ranking were later dropped on purpose |
| **Milestone 1** | Labelling guide, `eval_v0` (54 cases), fit-map API with exact offsets and strength rules, reproducible baseline incl. embeddings | Measure before building: a definition of "backed" and a baseline anyone can rerun |
| **Milestone 2** | Live site on Vercel + API on Cloud Run, backend-for-frontend, container, security headers, offline sample fallback | Ship a zero-cost public demo; Lighthouse 100 for accessibility, best practices and SEO (measured locally) |
| [`v2.0.0`](https://github.com/chintan-02/resumeiq/releases/tag/v2.0.0) | Matcher v2 + held-out `eval_v1`; resume upload, grounded drafting, claim checker, approval tokens; tailor plan, checklist, privacy mode, export | The full product loop, with AI drafting behind a deterministic gate |
| [`v2.1.0`](https://github.com/chintan-02/resumeiq/releases/tag/v2.1.0) | Claim-checker evaluation, structured logs, Error Reporting, API rate limits, uptime check and alert | Operate it safely: observability without logging resumes |
| [`v2.2.0`](https://github.com/chintan-02/resumeiq/releases/tag/v2.2.0) | Checker v1 and v2, live drafting runs `drafting_v0` and `drafting_v1`, model-client fixes (deprecated temperature, thinking tokens, empty replies) | Find real failure modes from real model output, then fix and re-measure |
| [`v2.3.0`](https://github.com/chintan-02/resumeiq/releases/tag/v2.3.0) | Matcher v3 (strength per named skill), checker v3 (directed synonyms), `eval_v2`, `claimcheck_v3`, `drafting_v2` | Fix a measured bug, and publish where held-out and live results disagree |

Milestone write-ups: [1 · fit map and baseline](docs/v2/MILESTONE_1.md) ·
[2 · live demo and deployment](docs/v2/MILESTONE_2.md) · [3 · uploads, drafting, approval](docs/v2/MILESTONE_3.md) ·
[Operations](docs/v2/OPERATIONS.md).

**Production incidents found and fixed along the way** (each one is in the history):

- AI drafting silently fell back to rules: the model had deprecated `temperature`. Fixed by sending it only when
  configured and logging every provider error.
- 22 of 24 live drafts came back empty: the model's default thinking consumed the output budget. Fixed by turning
  thinking off, raising the cap, and making the eval refuse to report when more than 25% of calls fail.
- Contact masking hid the first capitalised words of evidence lines in prompts. Fixed with a line-level mask.

## Run it locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e "apps/api[dev]"
uvicorn resumeiq_api.app:app --port 8000            # API on :8000

cd apps/web && npm install
RESUMEIQ_API_URL=http://127.0.0.1:8000 npm run dev  # site on http://localhost:3000
```

AI drafting is off unless `ANTHROPIC_API_KEY` is set; everything else works without it.

**Tests and reproducibility checks** (all run in CI on every push):

```bash
cd apps/api && pytest                      # 148 tests
cd apps/web && npm test && npm run build   # 20 tests + production build
python evals/run_baseline.py --check       # each --check fails if a committed report
python evals/run_eval_v1.py --check        # no longer reproduces exactly
python evals/run_eval_v2.py --check
python evals/run_claimcheck.py --check
```

Live drafting evaluation (needs a key, costs well under $0.10): `python evals/run_drafting_eval.py --set v2`.
Deployment: [Milestone 2](docs/v2/MILESTONE_2.md) (Vercel and Cloud Run) and
[Milestone 3](docs/v2/MILESTONE_3.md) (optional AI drafting).

## What I would do next

1. **Meaning-based echo check.** An embedding or model judge that asks "does the evidence entail this phrase?",
   used only to clear an echo flag, measured on a new frozen set.
2. **Verb-object matching.** Read *what* a strong verb applies to, so "led inventory planning" stops backing "lead
   data platform migrations".
3. **Human label review** of all held-out sets with the existing kit, then re-publish every number.

## Responsible use

ResumeIQ helps a candidate see and state their own evidence. It is decision support, not a hiring tool: it does not
score or rank people, and "no evidence found" means the documents do not show it, not that the person cannot do it.
All demo and evaluation data is synthetic.

## History

ResumeIQ began as *Smart Resume Classifier*, a Streamlit app with a role classifier, ATS-style scores and batch
ranking. That version is preserved at tag [`v0.9-legacy`](https://github.com/chintan-02/resumeiq/tree/v0.9-legacy). v2 is a rebuild around evidence:
its resume parsing, skill taxonomy, contact masking and bullet formula were ported from v0.9, while single-number
fit scores and candidate ranking were deliberately dropped.

## Author

Built by **Chintan Patel**, AI/ML developer in Edmonton, Canada. [GitHub](https://github.com/chintan-02)

## License

MIT

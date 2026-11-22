# Labelling guide: requirement → evidence

Version 0.1 · ResumeIQ v2, Milestone 1

This guide defines what counts as evidence. Every label in `evals/datasets/` must follow it,
and every matcher is judged against it. When the guide and your intuition disagree, follow the
guide and open an issue to change the guide. Do not quietly label by feel.

## The question you answer for each case

> Given **one job requirement** and **one candidate's evidence pool**, what does the evidence
> actually show the candidate did, and is that enough for the requirement?

You label the requirement, not the candidate. "Not found" means "this evidence pool does not
show it", never "this person cannot do it".

## Step 1: split the requirement into components

A requirement can bundle several things. List them before labelling.

| Requirement | Components |
| --- | --- |
| Deploy services with Docker and Kubernetes | Docker · Kubernetes · deploy services |
| Build and deploy ML models as REST APIs in production | build model API · deploy · production use |
| Experience with Python and scikit-learn | Python · scikit-learn |

Tool examples written as "such as X or Y" are alternatives: either satisfies that component.

## Step 2: read the required level

| Level | Name | Requirement wording that signals it |
| --- | --- | --- |
| L1 | Aware | familiarity with, exposure to, understanding of, knowledge of |
| L2 | Used | experience with, hands-on, proficiency in, use, work with |
| L3 | Built | build, design, develop, implement, deploy, write, automate, set up |
| L4 | Owned | lead, own, drive, architect, be responsible for, mentor |

## Step 3: read the evidence level

Judge what the **candidate personally did**, from the verb and its qualifiers, not from which
nouns appear.

| Level | Evidence wording | Example |
| --- | --- | --- |
| L0 | Keyword appears but the candidate didn't do the skill | "Presented SQL results from the analytics team" |
| L1 | Learned, read, studied, completed a course, attended, familiar with | "Completed an online course covering Kubernetes basics" |
| L2 | Used, applied, contributed to, assisted, helped, participated, reviewed | "Contributed to the team's deployment to Cloud Run" |
| L3 | Built, designed, developed, implemented, deployed, wrote, automated | "Wrote Dockerfiles for the API and a worker" |
| L4 | Led, owned, managed, architected, was responsible for | "Led the migration of three training pipelines to Vertex AI" |

Qualifiers lower the level: "contributed to the deployment" is L2 even though "deployment" is an
L3 noun; "helped prepare the report" is L2, not L4.

## Step 4: choose the status

| Status | Rule |
| --- | --- |
| **supported** | Every component is shown at or above the required level. An L1 requirement is supported by L1 evidence. |
| **partial** | Real experience exists (L2 or higher) but it is below the required level, covers only some components, or uses a related but different tool (MySQL for PostgreSQL). |
| **not_found** | No evidence of the core skill, or only L0/L1 evidence for a requirement at L2 or above. |

Then record:

- `gold_evidence_ids`: every evidence item needed to justify the status (empty for `not_found`).
- `gold_quote`: the shortest exact substring of one gold evidence item that carries the claim.
- `rationale`: one sentence a reviewer can check.
- `trap: true` when the right keyword appears but the evidence supports a weaker claim or a
  different meaning. These cases exist to catch matchers that count words.
- `ambiguous: true` when two careful reviewers could reasonably disagree. Ambiguous cases go to
  the second reviewer first.

## Worked examples

| Requirement (level) | Evidence | Status | Why |
| --- | --- | --- | --- |
| Lead deployment to a cloud platform (L4) | "Contributed to the team's deployment of the service to Google Cloud Run." | partial | L2 contribution to an L4 requirement |
| Familiarity with Kubernetes (L1) | "Completed an online course covering Kubernetes basics." | supported | L1 evidence meets an L1 requirement |
| Hands-on experience with Docker (L2) | "Read about Docker and containerization while preparing for interviews." | not_found | L1 only, requirement is L2 |
| Deploy with Docker and Kubernetes (L3) | "Containerized the API with Docker; the platform team handled the Kubernetes deployment." | partial | Docker shown, Kubernetes done by others |
| Write SQL to build training datasets (L3) | "Presented SQL query results from the analytics team at weekly meetings." | not_found | L0: keyword present, skill not performed |

## Rules for the datasets

1. **Synthetic only.** No real person's resume text, no scraped job postings. Invented
   companies and people only.
2. **The public demo sample is never evaluated.** `apps/api/src/resumeiq_api/samples/` is a
   walkthrough, not test data. A test enforces that no demo evidence text appears in an eval pool.
3. **Disjoint families.** Candidates and job-description families in `dev` never appear in
   `test`. Thresholds are tuned on `dev` only.
4. **Label status is tracked.** `draft` = written but not reviewed; `reviewed` = checked by a
   second person; `adjudicated` = disagreement resolved, with a note. Report numbers from
   `draft` labels as provisional.
5. **Change the guide, then relabel.** If a case shows the guide is wrong, bump the guide version,
   relabel affected cases, and note it in the report.

# Claim checker report: check_claim v3 on held-out claimcheck_v3

Test set `claimcheck_v3` · sha256 `6c7e0b42e30c` · labels ai-drafted · package 0.1.0

> **Provisional.** Cases and labels were drafted by an AI assistant that also wrote checker v3, and have not
> had a human review. claimcheck_v3 was written and frozen before the synonym map existed, and only its
> totals under checker v2 were looked at before the change. The same author picked both the synonym pairs in
> the set and the map, so the honest-synonym result is optimistic; the live drafting run is the fairer test.

The claim checker is the gate between a drafted bullet and approval. It must block drafts that claim more
than the cited evidence shows, and let honest rewrites through. v2 blocked every clear overstatement in live
drafting, but its false alarms were honest synonyms ("findings" for an analysis, "LLM" for a language
model). v3 adds a directed synonym map: a claim word passes only if the evidence has a word that justifies
it ("stakeholders" from "managers", never "executives" from "team lead"). It applies to the echo and
tool checks only, so a synonym can never raise a verb level, a number or a scope.

| Measure | Result | 95% CI |
| --- | --- | --- |
| Overstated drafts blocked | 20/20 (100%) | 84%–100% |
| Honest drafts wrongly blocked | 3/20 (15%) | 5%–36% |

Before and after, on the same held-out set:

| Checker | Overstated blocked | Honest wrongly blocked |
| --- | --- | --- |
| v2 (commit ddff2a4) | 20/20 (100%) | 15/20 (75%) |
| **v3 (current)** | **20/20 (100%)** | **3/20 (15%)** |

On the development sets v3 was designed on: claimcheck_v0 blocks 44/44 and wrongly blocks 0/30; claimcheck_v1 blocks 34/34 and wrongly blocks 0/26; claimcheck_v2 blocks 26/26 and wrongly blocks 2/29. That shows the rules do what they were built for, not how well they generalise; the held-out numbers above do.

## By category

| Category | Should | Blocked |
| --- | --- | --- |
| Wording copied from the job posting | block | 6/6 |
| Earlier rules (verbs, numbers, tools, scope, team, outcomes) | block | 6/6 |
| Look-alike word that adds a claim (executive for team lead) | block | 8/8 |
| Earlier honest cases (rewording, weaker, formats) | pass | 1/6 |
| Honest synonym of the evidence (findings for analysis, LLM for language model) | pass | 2/14 |

## Every error

| Case | Category | Should | Evidence | Draft | Checker said |
| --- | --- | --- | --- | --- | --- |
| CF011 | synonym_honest | pass | Grouped 800 survey comments into themes in a spreadsheet. | Analysed 800 survey comments by grouping them into themes in a spreadsheet. | It claims use, but the evidence shows awareness. Keep the verb as strong as what you did.; Wording from the job posting that your evidence does not show: analysed. Keep only what you did. |
| CF012 | synonym_honest | pass | Removed duplicate rows and fixed date formats in the vendor file. | Cleaned the vendor file by removing duplicate rows and fixing date formats. | It claims use, but the evidence shows awareness. Keep the verb as strong as what you did. |
| CF039 | regression_pass | pass | Deployed the scorer to k8s with a Helm chart. | Deployed the scorer to Kubernetes with a Helm chart. | Wording from the job posting that your evidence does not show: kubernetes. Keep only what you did. |

Reproduce: `python evals/run_claimcheck.py --check`

## Notes on the v3 result

**Errors (3 honest drafts blocked, 0 overstatements missed).** None was changed in response:

- CF011 and CF012: the evidence verbs "grouped" and "removed" are not in the shared verb list, so the line reads as
  awareness and the honest draft ("analysed", "cleaned") looks like a stronger claim. That is the level rules in
  `levels.py`, which the matcher shares; changing it needs its own frozen set for both.
- CF039: the tool check knows `k8s` is Kubernetes, but the echo check does not, so "Kubernetes" in the draft is
  read as copied from the posting. A one-line fix (share the tool aliases with the echo check), for the next set.

**Open labelling question (from the AI second-pass review).** The reviewer marked CE048 ("reducing [error type] by
[amount]") as an overstatement, because the draft still claims a reduction. Four development cases with the same
shape (CC063, CC064, CD046, CD047) are labelled honest: the guide treats an outcome followed by placeholders as a
template the person must fill or delete. v3 keeps the guide's policy. A human reviewer should decide; if the policy
changes, all five labels change together and the rule gets a new frozen set.

**Development checks.** On claimcheck_v0–v2 nothing changed (one issue message on CE005 lost "stakeholders", still
blocked). On the stored live drafts, v3 passes the three known false alarms (DS015, DS021, DS023) and one retry
that was borderline ("sharing results with stakeholders to inform their decisions"), which is the trade a synonym
map makes.

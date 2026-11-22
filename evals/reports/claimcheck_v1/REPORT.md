> **Historical.** This is the report for checker v1. The current checker (v2) is measured on a new held-out
> set in [claimcheck_v2](../claimcheck_v2/REPORT.md); claimcheck_v1 became one of its development sets.

# Claim checker report: check_claim v1 on held-out claimcheck_v1

Test set `claimcheck_v1` · sha256 `eb354397a6fc` · labels ai-drafted · package 0.1.0

> **Provisional.** Cases and labels were drafted by an AI assistant that also wrote checker v1, and have not
> had a human review. claimcheck_v1 was written and frozen before any v1 change, and only its totals under
> the old checker were looked at before the change. Hard cases were included on purpose.

The claim checker is the gate between a drafted bullet and approval. It must block drafts that claim more
than the cited evidence shows, and let honest rewrites through.

| Measure | Result | 95% CI |
| --- | --- | --- |
| Overstated drafts blocked | 33/34 (97%) | 85%–100% |
| Honest drafts wrongly blocked | 0/26 (0%) | 0%–13% |

Before and after, on the same held-out set:

| Checker | Overstated blocked | Honest wrongly blocked |
| --- | --- | --- |
| v0 (v0 (commit 4b5e1ff)) | 15/34 (44%) | 1/26 (4%) |
| **v1 (current)** | **33/34 (97%)** | **0/26 (0%)** |

On claimcheck_v0, which v1 was designed on, v1 blocks 44/44 and wrongly blocks 0/30. That is development data, so it shows the rules do what they were built for, not how well they generalise; the held-out numbers above do.

## By category

| Category | Should | Blocked |
| --- | --- | --- |
| Changed number | block | 3/3 |
| Invented outcome, no number (significantly reduced…) | block | 5/5 |
| Invented number | block | 3/3 |
| Invented tool | block | 4/4 |
| Wider scope, no new number (production, all, end-to-end) | block | 5/5 |
| Team work claimed alone | block | 3/3 |
| Stronger verb (common words) | block | 5/6 |
| Stronger verb (synonyms: steered, chaired…) | block | 5/5 |
| Faithful rewording | pass | 0/6 |
| Same number, different format | pass | 0/4 |
| Outcome as a placeholder | pass | 0/2 |
| Outcome that is in the evidence | pass | 0/2 |
| Placeholders for missing facts | pass | 0/3 |
| Scope word that is in the evidence | pass | 0/3 |
| Team work, team kept | pass | 0/1 |
| Same tool, different name | pass | 0/2 |
| Same or weaker claim | pass | 0/3 |

## Every error

| Case | Category | Should | Evidence | Draft | Checker said |
| --- | --- | --- | --- | --- | --- |
| CD001 | verb_escalation | block | Helped refactor the billing service's retry logic. | Refactored the billing service's retry logic. | passed |

Reproduce: `python evals/run_claimcheck.py --check`

## What changed in checker v1

All changes are in `rewrite.py` (the claim side). `levels.py` is shared with the matcher and was not touched,
so every matching score is unchanged.

- Numbers are compared after normalising: `12 %` equals `12%`, and number words equal digits (`two` = `2`).
- Leadership verbs beyond the matcher's list (orchestrated, championed, steered, chaired, oversaw…) count as
  claiming ownership.
- Team work claimed alone is blocked: evidence such as "one of four engineers who rebuilt…" or "worked on a team
  that…" must keep the team in the bullet.
- Scope words not in the evidence are blocked: production, all, entire, end-to-end, real-time, company-wide,
  independently, every (except time periods such as "every month").
- Outcomes not in the evidence are blocked ("reducing…", "leading to…", "which sped up…", "significantly"),
  unless the outcome is written as a placeholder.

## How to read the result

**Held-out improvement is large:** 15/34 to 33/34 overstated drafts blocked, with no honest draft blocked.

**It is probably optimistic.** The same author wrote claimcheck_v1 and the v1 rules. The set was frozen before any
rule was written and only its totals were seen beforehand, but the author knew which kinds of overstatement v1
would target. Two checks that do not share this bias:

1. **Live drafting evaluation** (`evals/run_drafting_eval.py`): the real model's drafts, not drafts written to
   test the rules.
2. **Human label review** (`evals/review/`): a person who did not write the rules confirms or corrects each label.

**The remaining miss shows the limit of word lists.** "Helped refactor…" became "Refactored…": "refactored" is not
in any verb list, so the level check could not see the jump. A rule-based checker only knows the words it was given;
the human approval step is still required.

**The cost of the new rules:** scope and outcome words that are not in the evidence are now blocked even when a
user means them honestly. The fix is to add the fact to the evidence (the resume line) first, which is the
behaviour ResumeIQ wants anyway.

## Run history

claimcheck_v1 was scored once with checker v1. Afterwards, a unit test found that outcome phrases of more than
one word ("leading to…") were compared on the wrong word, so "leading to" could look stated whenever the evidence
contained "to". The fix changed no result on claimcheck_v1 (the report above reproduces exactly) and none on
claimcheck_v0.

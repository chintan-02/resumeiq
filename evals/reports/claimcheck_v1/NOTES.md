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

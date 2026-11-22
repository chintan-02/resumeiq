# Claim checker report: check_claim v2 on held-out claimcheck_v2

Test set `claimcheck_v2` · sha256 `35943e6486c8` · labels ai-drafted · package 0.1.0

> **Provisional.** Cases and labels were drafted by an AI assistant that also wrote checker v2, and have not
> had a human review. claimcheck_v2 was written and frozen before any v2 change, and only its totals under
> checker v1 were looked at before the change. Hard cases were included on purpose.

The claim checker is the gate between a drafted bullet and approval. It must block drafts that claim more
than the cited evidence shows, and let honest rewrites through. In v2 every case also carries the job
requirement, because the main failure seen in live drafting was wording copied from the posting.

| Measure | Result | 95% CI |
| --- | --- | --- |
| Overstated drafts blocked | 26/26 (100%) | 87%–100% |
| Honest drafts wrongly blocked | 2/29 (7%) | 2%–22% |

Before and after, on the same held-out set:

| Checker | Overstated blocked | Honest wrongly blocked |
| --- | --- | --- |
| v1 (v1 (commit 8478f65)) | 9/26 (35%) | 6/29 (21%) |
| **v2 (current)** | **26/26 (100%)** | **2/29 (7%)** |

On the development sets v2 was designed on: claimcheck_v0 blocks 44/44 and wrongly blocks 0/30; claimcheck_v1 blocks 34/34 and wrongly blocks 0/26. That shows the rules do what they were built for, not how well they generalise; the held-out numbers above do.

## By category

| Category | Should | Blocked |
| --- | --- | --- |
| Posting outcome claimed, amount as placeholder | block | 4/4 |
| Earlier rules (verbs, numbers, tools, scope, team, outcomes) | block | 8/8 |
| Wording copied from the job posting | block | 12/12 |
| Scope word without hyphens (real time, end to end) | block | 2/2 |
| Posting words that are in the evidence | pass | 0/8 |
| Only generic words shared with the posting | pass | 1/5 |
| Scope word that the draft denies | pass | 1/4 |
| Placeholders for missing facts | pass | 0/3 |
| Earlier honest cases (rewording, weaker, formats) | pass | 0/6 |
| Team work, team kept | pass | 0/3 |

## Every error

| Case | Category | Should | Evidence | Draft | Checker said |
| --- | --- | --- | --- | --- | --- |
| CE036 | generic_overlap | pass | Cleaned the vendor files with pandas each Monday. | Cleaned the vendor files with pandas every Monday. | Wider scope than your evidence: every. Say only what the evidence covers. |
| CE043 | negation | pass | Piloted the forecasting tool in one region. | Piloted the forecasting tool in one region before any company-wide rollout. | Wider scope than your evidence: company-wide. Say only what the evidence covers.; Wording from the job posting that your evidence does not show: company-wide, rollout. Keep only what you did. |

Reproduce: `python evals/run_claimcheck.py --check`

## What changed in checker v2

All changes are in `rewrite.py` (the claim side); `levels.py`, shared with the matcher, is untouched, so every
matching score is unchanged. The checker now receives the job requirement as well as the evidence.

- **Wording copied from the job posting** is blocked: a draft word that appears in the requirement but not in the
  evidence ("supporting mentorship of junior engineers" from evidence about code reviews). Words are compared by
  their first five letters (mentor, mentoring, mentorship), short words by containment ("APIs" in "FastAPI"), and a
  list of generic words (data, team, model, build, experience…) never counts.
- **Negation:** spans after not, never, no, rather than, instead of or without are not claims ("rather than a
  real-time stream").
- **Spelling:** "real time" and "end to end" count like their hyphenated forms.
- **Rebuilding verbs** (rebuilt, refactored, rewrote, redesigned…) count as building, unless the line is qualified
  ("helped refactor"). This fixes v1's one miss and the live false alarm on "one of four engineers who rebuilt".
- **Placeholders no longer hide an invented outcome:** "reducing cloud costs by [X]" claims that costs went down;
  "reducing [cost type] by [amount]" is a shape to fill and still passes.
- The approval token now also binds the requirement, so a check without it cannot approve a draft for it.

## How to read the result

**Held-out:** 9/26 to 26/26 overstated drafts blocked, and 6/29 to 2/29 honest drafts wrongly blocked.

**It is optimistic.** The same author wrote claimcheck_v2 and the v2 rules. The set was frozen before any rule was
written and only its totals were seen beforehand, but the author knew which failure the rules would target. The
independent check is the live run on `drafting_v1` (real model drafts on requirements the rules never saw) plus a
human review.

**The two false blocks show where word rules stop:**

- "Cleaned the vendor files with pandas every Monday": the "every [time period]" exception knows day, week and month,
  not weekday names.
- "Piloted the tool in one region before any company-wide rollout": "before any" denies the scope, but it is not in
  the negation list.

**Known limit found on development data:** synonyms. "Non-technical" in a draft against "plain language" in the
evidence is blocked as posting wording, because no word rule can tell they mean the same thing. In production the
retry names the word, so the model usually drops it at the cost of one extra call.

**The cost of the new rule:** a user who really did something the posting names, but did not say so in the resume
line, is told to add it to the evidence first. That is the behaviour ResumeIQ wants: the resume line is the source of
truth.

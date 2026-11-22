> **Historical.** This is the report for checker v0. The current checker (v1) is measured on a new held-out
> set in [claimcheck_v1](../claimcheck_v1/REPORT.md); claimcheck_v0 became its development set.

# Claim checker report: check_claim on claimcheck_v0

Test set `claimcheck_v0` · sha256 `4634e93fb6cd` · labels ai-drafted · package 0.1.0

> **Provisional.** Cases and labels were drafted by an AI assistant that also knew how the checker works,
> and have not had a human review. The set was frozen before the checker was run on it, and the checker
> was not changed afterwards. Categories the checker was expected to miss were included on purpose.

The claim checker is the gate between a drafted bullet and approval. It must block drafts that claim more
than the cited evidence shows, and let honest rewrites through.

| Measure | Result | 95% CI |
| --- | --- | --- |
| Overstated drafts blocked | 33/44 (75%) | 61%–85% |
| Honest drafts wrongly blocked | 2/30 (7%) | 2%–21% |

## By category

| Category | Should | Blocked |
| --- | --- | --- |
| Changed number | block | 4/4 |
| Invented outcome, no number (significantly reduced…) | block | 1/4 |
| Invented number | block | 6/6 |
| Invented tool | block | 6/6 |
| Wider scope, no new number (production, all, end-to-end) | block | 1/6 |
| Stronger verb (common words) | block | 9/10 |
| Stronger verb (synonyms: spearheaded, drove…) | block | 6/8 |
| Faithful rewording | pass | 0/10 |
| Same number, different format | pass | 2/5 |
| Placeholders for missing facts | pass | 0/5 |
| Same tool, different name | pass | 0/4 |
| Same or weaker claim | pass | 0/6 |

## Every error

| Case | Category | Should | Evidence | Draft | Checker said |
| --- | --- | --- | --- | --- | --- |
| CC008 | verb_escalation | block | Worked on a team that rebuilt the search ranking model. | Rebuilt the search ranking model. | passed |
| CC014 | verb_synonym | block | Assisted in coordinating the quarterly model retraining. | Orchestrated the quarterly model retraining. | passed |
| CC015 | verb_synonym | block | Contributed to an internal push for better data documentation. | Championed an internal push for better data documentation. | passed |
| CC035 | scope_words | block | Built a prototype dashboard for the sales team. | Built a production dashboard for the sales team. | passed |
| CC036 | scope_words | block | Wrote unit tests for the billing module. | Wrote unit tests for every module in the billing platform. | passed |
| CC037 | scope_words | block | Cleaned survey data for one regional study. | Cleaned survey data for all regional studies. | passed |
| CC038 | scope_words | block | Built part of the data pipeline for the recommendation model. | Built the end-to-end data pipeline for the recommendation model. | passed |
| CC039 | scope_words | block | Built a batch scoring job that runs nightly. | Built a real-time scoring service. | passed |
| CC041 | invented_outcome | block | Built a FastAPI service that serves the churn model to the billing team. | Built a FastAPI service that serves the churn model to the billing team, significantly reducing churn. | passed |
| CC042 | invented_outcome | block | Rewrote the ETL job in PySpark. | Rewrote the ETL job in PySpark, dramatically improving reliability. | passed |
| CC043 | invented_outcome | block | Added input validation to the upload endpoint. | Added input validation to the upload endpoint, eliminating data quality issues. | passed |
| CC067 | number_format | pass | Cut report runtime by 12% with indexing. | Cut report runtime by 12 % with indexing. | Numbers not in your evidence: 12 %. Use [add measurable result] instead. |
| CC069 | number_format | pass | Supported two product teams with weekly analyses. | Supported 2 product teams with weekly analyses. | Numbers not in your evidence: 2. Use [add measurable result] instead. |

Reproduce: `python evals/run_claimcheck.py --check`

## What this shows

**Strong where facts can be checked.** Every invented or changed number and every invented tool was blocked
(16/16). These are the claims a recruiter can verify in an interview, and the checker compares them against the
cited text exactly.

**Mostly right on verbs.** 15 of 18 stronger-verb drafts were blocked. The misses are verbs without a clear
strength in the rules ("orchestrated", "championed") and one case where the evidence describes a team ("worked on a
team that rebuilt…") and the draft takes sole credit with the same verb ("rebuilt").

**Weak on meaning.** Drafts that widen scope with words rather than numbers ("production", "every module",
"end-to-end", "real-time") and drafts that add an outcome without a number ("significantly reducing churn") mostly
pass. The checker compares verbs, numbers and tools; it does not understand what a phrase claims.

**False blocks lean safe.** Both honest drafts that were blocked are number formats: "12 %" with a space (a bug in
how numbers are normalised) and "two" written as "2". A false block costs the user a reword; a miss costs trust.

## Why this is not a release blocker

The checker is one of three safeguards. Drafts never replace a line automatically: the user sees the cited evidence
next to the draft, must approve it, and an edited draft has to pass the check again. Placeholders such as
`[add measurable result]` keep missing facts visible. The gaps above are where that human review matters most.

## Next version (claimcheck_v1)

Planned changes, to be measured on a new frozen set rather than on this one:

1. Normalise numbers before comparing (spacing before `%`, number words such as "two").
2. Add the missed verbs to the strength rules (orchestrated, championed and similar), and treat a team-to-sole
   change ("worked on a team that rebuilt" to "rebuilt") as an escalation.
3. Flag scope words that are not in the evidence (production, all, every, end-to-end, real-time,
   company-wide, single-handedly).
4. Flag outcome phrases that are not in the evidence (reducing, improving, eliminating, leading to) unless they
   use a placeholder.

The cost of 3 and 4 is more false blocks on honest drafts, so v1 must report both rates side by side.

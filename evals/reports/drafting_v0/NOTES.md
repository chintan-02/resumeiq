# Audit notes for the live drafting run (2026-11-22)

> **Audit by an AI assistant, not a human review.** It reads every case in REPORT.md against its evidence. A human
> review with `evals/review/review_drafting_v0.csv` is still pending, so treat these counts as provisional.

## Were the four blocked first drafts real overstatements?

| Case | What the first draft added | Verdict |
| --- | --- | --- |
| DR001 | "to AWS production" | Real: the evidence does not say production |
| DR016 | "a foundation for production machine learning work" | Real, mild: implies a link to production |
| DR017 | "batch rather than real-time" | False alarm: the draft denies real-time; the checker cannot read negation |
| DR019 | "Contributed to rebuilding … as one of four engineers" | False alarm: honest, but the checker read "Was one of four engineers who rebuilt" as awareness only, because "rebuilt" is not in its verb list. The retry was blocked for the same reason and the case fell back to the rule-based shape |

So the model's first drafts overstated in a way the checker could see in **2 of 24** cases, and the checker raised
**2 false alarms**. One retry also passed by writing "real time" without a hyphen, which the scope rule does not match.

## Did any draft that passed overstate?

Of the 23 final drafts written by the model:

- **4 clearly add a claim the evidence does not support:** DR003 "supporting mentorship of junior engineers"
  (evidence: code reviews only), DR004 "contributing input toward the analytics platform roadmap", DR013 "for
  improved model accuracy", and DR014 "reducing cloud spend by [add measurable result]". In DR014 the placeholder
  hides the amount, but the claim that spend went down is itself invented.
- **5 are borderline:** DR008 "supporting reliable daily data delivery", DR010 "recording training runs and results
  for team review", DR015 "reducing manual reporting effort", DR018 "contributing to early data quality practices",
  DR020 "a customer-facing ML feature".
- The other 14 stay within their evidence.

## The pattern

The model rarely inflates verbs, numbers or tools, which the checker covers. It inflates by **echoing the job
requirement into an added clause**: mentorship, roadmap, accuracy, production. The checker compares a draft with its
evidence but never asks whether a phrase came from the requirement instead.

## Next version (to be measured on a new drafting set, not this one)

1. Flag content words that the draft shares with the requirement but not with the evidence (requirement echo).
2. Read negation before scope words ("rather than real-time", "not in production").
3. Match "real time" as well as "real-time".
4. Read "rebuilt" and team phrasing ("one of four engineers who rebuilt") as building, so honest team drafts pass.
5. Treat an outcome verb before a placeholder ("reducing [X]") as an outcome claim unless the evidence states it.

These changes were found on this run, so measuring them on it would grade the fix on its own answer key. They need a
fresh set (drafting_v1) written before the code changes.

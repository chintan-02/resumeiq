# Notes on the drafting_v2 run (checker v3)

AI audit of every block and every final model draft. Provisional: an AI assistant wrote the checker, the set and
this audit. A person should confirm it with `evals/review/review_drafting_v2.csv`.

## Were the 15 blocks right?

**6 real overstatements.**

| Case | What the first draft added |
| --- | --- |
| DT010 | "to production"; the evidence is a staff-only beta site |
| DT012 | "roadmap discussions and cross-team alignment" from attending meetings |
| DT013 | "reducing infrastructure spend"; no result in the evidence |
| DT014 | "fairness and compliance metrics" from a retrain |
| DT015 | "Reviewed" for "Read" |
| DT017 | "supporting scalable model training" from one scaling step |

**5 borderline.** Reasonable inferences, but they add something the evidence does not say.

| Case | Draft wording | Why borderline |
| --- | --- | --- |
| DT004 | "non-technical stakeholders" | The audience is inferred |
| DT007 | "for technical users" | The audience is inferred |
| DT009 | "clean and validate the data" | Validate is a stretch. The level message is a known false alarm: "removed" is not in the verb list |
| DT011 | "feedback to engineers on code quality" | Close to what reviewing pull requests is |
| DT019 | "reducing reliance on recurring vendor costs" | A consequence, not a stated result |

**4 false alarms.** Honest synonyms or descriptions that are not in the synonym map.

| Case | Draft wording | Evidence |
| --- | --- | --- |
| DT005 | "a basic data quality check" | Counting rows |
| DT006 | "track model performance" | Logging accuracy. This one fell back to the rule-based shape. |
| DT008 | "executive-level" | A vice president |
| DT016 | "cloud data warehouse" | BigQuery |

## Did any final model draft overstate?

No clear case. 3 of 15 are borderline:

| Case | Wording | Issue |
| --- | --- | --- |
| DT003 | "into models" | "model" is on the generic-word list, so the echo of the requirement's "model" is not checked |
| DT004 | "translating findings into decisions they could act on" | Inferred purpose |
| DT012 | "contributing to ongoing discussions" | From "attended" |

## What this run says about checker v3

- **The pairs v3 added hold up live.** DT001 ("findings" for an analysis), DT002 (language model) and DT003
  ("reshaped") passed on the first draft. With checker v2, the same kind of wording was blocked in drafting_v1.
- **Live false alarms did not fall.** 4 of 15 blocks here, against 3 of 19 with v2 on drafting_v1. These are
  different sets, so this is not a strict comparison. Each false alarm was a new synonym or a broader word for an
  evidence word: quality check, performance, executive, cloud warehouse.
- **The held-out result was optimistic.** On claimcheck_v3, wrongly blocked honest drafts fell from 15/20 to 3/20.
  The same author chose the pairs in that set and in the map, as its report warns. A hand-written list fixes the
  pairs it lists and little else.
- **Safety held.** No clear overstatement reached a final model bullet. 5 of 20 fell back to the rule-based shape,
  and 1 of those (DT006) was honest. That one lost bullet is the measured cost of the remaining false alarms.

## Decision

- **Keep v3.** It removed known false alarms and missed no real overstatement on any set.
- **Stop growing the list.** Adding these four pairs would overfit this run. The next step is a semantic check, used
  only to clear echo flags: does the evidence entail this phrase? An embedding or model judge would do this. It
  needs its own frozen set and must never pass a draft that the level, number, tool or scope rules block.

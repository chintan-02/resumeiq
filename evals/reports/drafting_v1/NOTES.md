# Audit notes for the live drafting run with checker v2 (2026-11-22)

> **Audit by an AI assistant, not a human review.** It reads every case in REPORT.md against its evidence and
> requirement. A human review with `evals/review/review_drafting_v1.csv` is still pending, so these counts are
> provisional.

`drafting_v1` is a fresh set that the v2 rules never saw. Most of its requirements tempt the model to echo their
wording, the failure found in the first live run.

## Were the 19 blocked first drafts real overstatements?

**15 real catches**, mostly wording copied from the posting: DS002 "to inform growth experimentation", DS004
"supporting data-informed decisions", DS005 "a reliable data pipeline", DS006 "reproducible builds", DS007 "the move
of analytics to a modern cloud warehouse", DS009 "their analyst work", DS020 "a new ML product"; invented outcomes:
DS003 "improving accuracy by [X]", DS010 "churn reduction", DS011 "to reduce infrastructure spend", DS012 "reducing
cycle time by [X]", DS022 "reducing manual data entry"; wider scope: DS016 "potential production use", DS017
"real-time delivery", DS018 "its end-to-end workflow".

**1 borderline:** DS001 "providing technical feedback": reviewing pull requests implies feedback, but "technical"
came from the posting.

**3 false alarms:**

| Case | Draft | Why it is honest |
| --- | --- | --- |
| DS015 | "transforming source data for reporting" | SQL views do transform data; a description, not a claim |
| DS021 | "LLM fine-tuning techniques" | The evidence says "language models"; a synonym |
| DS023 | "churn analysis findings" | Presenting an analysis is presenting findings. The retry also failed, so this case fell back to the rule-based shape |

## Did any final model draft overstate?

None of the 20 final model drafts clearly overstates its evidence. Two are borderline: DS008 "contributing to an
event-driven data pipeline" (one Kafka consumer of order events is arguably part of one) and DS009 "keeping their work
on track".

For comparison, the first live run (`drafting_v0`, checker v1) let 4 clear overstatements through out of 23 model
drafts. Different sets, so this is not a strict before and after, but the gap is the failure v2 was built to close.

## The cost

- 3 false alarms in 19 blocks. The retry fixed 2; one honest case (DS023) ended on the rule-based shape.
- All 3 are synonyms or descriptions ("findings", "transforming", "LLM"), which word rules cannot tell from new
  claims.
- DS016 also got a misleading level message ("the evidence shows awareness"): "tested" is not in the matcher's verb
  list. The block itself was right (wider scope).

## Next, if needed

A synonym list for the most common cases (findings/analysis, LLM/language model, transforming/views), measured on a
new set. The current trade, catching every clear overstatement for a few retries, is acceptable for a safety check.

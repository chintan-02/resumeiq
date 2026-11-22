# Held-out report: matcher v2 on eval_v1

Test set `eval_v1` · sha256 `a211038541f4` · labels {'ai-drafted': 36} · labelling guide v0.1 · package 0.1.0

> **Provisional.** Labels were drafted by an AI assistant and have not had a human review. The same author
> wrote the test set and matcher v2; the set was written and frozen before any v2 code, and no threshold or
> rule was tuned on it. 36 cases is small, so the confidence intervals are wide.

All matchers were tuned on eval_v0 (dev and test together) and scored once on eval_v1, which has new job
families and candidates aimed at v1's known failures: compound requirements, `A/B` and `such as`
alternatives, paraphrases and keyword traps.

| Matcher | Macro-F1 [95% CI] | Accuracy | Trap cases correct | Evidence recall@1 | Evidence recall@3 | Citation precision |
| --- | --- | --- | --- | --- | --- | --- |
| `keyword` | 0.49 [0.31, 0.65] | 0.50 | 0/4 | 0.81 | 0.89 | 0.61 |
| `keyword-rules` | 0.60 [0.42, 0.75] | 0.64 | 3/4 | 0.81 | 0.89 | 0.81 |
| `keyword-rules-v2` | 0.73 [0.56, 0.88] | 0.75 | 3/4 | 0.89 | 0.93 | 0.76 |

Thresholds (tuned on eval_v0): `keyword` low 0.3, high 0.65, `keyword-rules` low 0.3, high 0.35, `keyword-rules-v2` low 0.3, high 0.35

## Errors of `keyword-rules-v2` on eval_v1

| Case | Gold | Predicted |
| --- | --- | --- |
| C7-J5-R5 | supported | not_found |
| C7-J5-R6 | supported | partial |
| C7-J5-R7 | supported | not_found |
| C8-J5-R3 | partial | not_found |
| C8-J5-R6 | partial | not_found |
| C8-J5-R8 | not_found | partial |
| C9-J6-R6 | not_found | supported |
| C10-J6-R4 | partial | supported |
| C10-J6-R5 | partial | supported |

## Run history

eval_v1 has been scored twice. Run 1 (macro-F1 v2 0.73, v1 0.60, naive 0.49) exposed nothing that was
changed in response. Between runs, a unit test written for the v2 spec found that `FastAPI/Flask` was not
read as either/or (synonym expansion split the option). That bug was fixed, dev scores were unchanged
(eval_v0 macro-F1 0.839, same thresholds), and the table above is run 2. No other change was made.

Reproduce: `python evals/run_eval_v1.py --check`

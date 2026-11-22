# Held-out report: matcher v3 on eval_v2

Test set `eval_v2` · sha256 `5ef74f0771f9` · labels {'ai-drafted': 34} · labelling guide v0.1 · package 0.1.0

> **Provisional.** Labels were drafted by an AI assistant and have not had a human review. The same author
> wrote the test set and matcher v3, which makes these numbers optimistic. The set was frozen before any v3
> code and no threshold or rule was tuned on it. 34 cases is small, so the confidence intervals are wide
> and overlap: read the difference as direction, not proof.

**What v3 changes.** v2 judged strength from the strongest cited line, so `Skills: Looker` plus an
unrelated `Built weekly sales reports` could read as building Looker dashboards. v3 judges each named
tool or skill in the requirement (words the posting capitalises: Airflow, SQL, Docker) by the best line
that actually mentions it, and the requirement by the weakest of those. Generic words (data, model, test)
keep v2's rule, because an early version that judged them too lost accuracy on dev.

| Matcher | Dev macro-F1 | Held-out macro-F1 [95% CI] | Accuracy | Trap cases correct | Evidence recall@3 |
| --- | --- | --- | --- | --- | --- |
| `keyword-rules-v2` | 0.79 | 0.69 [0.52, 0.88] | 0.82 | 9/12 | 0.95 |
| `keyword-rules-v3` | 0.80 | 0.77 [0.55, 0.95] | 0.85 | 9/12 | 0.95 |

Thresholds (tuned on dev): `keyword-rules-v2` low 0.3, high 0.35, `keyword-rules-v3` low 0.3, high 0.35

Decision: v3 changed 2 of 90 dev answers, both toward the gold label, and none away from it, so it met
the adoption rule. It is the default matcher from this release; v2 stays in the code for comparison.

## Errors of `keyword-rules-v3` on eval_v2

| Case | Gold | Predicted | Why |
| --- | --- | --- | --- |
| C12-J7-R4 | not_found | supported | Strong verb, wrong work: 'Led the quarterly inventory planning process' is read as leading. |
| C12-J7-R5 | partial | not_found | Excel reports are a related tool (partial); v3 sees Looker only listed and says not found. |
| C13-J8-R6 | partial | not_found | Pairing with one graduate is mentoring-like (partial, ambiguous); no keyword overlap. |
| C14-J8-R3 | partial | supported | Built REST endpoints, but not for model serving; keywords cannot see the missing purpose. |
| C14-J8-R4 | not_found | supported | Strong verb, wrong work: 'Responsible for monitoring the office network' is read as owning monitoring. |

Trap accuracy did not move (9/12 for both). Two of the three trap misses are a different failure: a
strong verb attached to the wrong work. Telling 'led inventory planning' from 'led a data platform
migration' needs the object of the verb, which a keyword matcher does not read. That is the next
target, and it needs a new frozen set when it is attempted. The third (C12-J7-R5) is v3 being stricter
than the guide: a related tool (Excel for Looker) counts as partial, and v3 does not know tools are related.

Reproduce: `python evals/run_eval_v2.py --check`

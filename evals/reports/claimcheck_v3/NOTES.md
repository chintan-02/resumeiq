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

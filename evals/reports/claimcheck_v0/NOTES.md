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

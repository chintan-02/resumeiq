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

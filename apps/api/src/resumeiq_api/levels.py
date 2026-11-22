"""Rule-based strength levels for evidence and requirements.

These rules implement Steps 2 and 3 of evals/LABELING_GUIDE.md. They are a
deliberately simple, explainable baseline: they read verbs and qualifiers, not
meaning. The evaluation report shows where they fail (for example, they cannot
tell that "Presented SQL results from another team" means the candidate did not
write the SQL).
"""

from __future__ import annotations

import re

from .models import Level

_OWNED = r"\b(led|lead|leads|leading|owned|own|owns|managed|manage|architected|architect|headed|directed|spearheaded|mentored|mentor|drove|drive|responsible for)\b"
_BUILT = (
    r"\b(built|build|designed|design|developed|develop|implemented|implement|deployed|deploy|"
    r"created|create|wrote|write|automated|automate|packaged|trained|modell?ed|containeri[sz]ed|"
    r"added|scheduled|set up|configured|migrated|launched|shipped|engineered|delivered)\b"
)
_USED = (
    r"\b(used|use|uses|using|applied|worked with|work with|processed|stored|queried|cleaned|clean|"
    r"analy[sz]ed|analy[sz]e|explained|explain|communicate|presented|logged|tracked|compared|"
    r"reported|maintained|checked|ran|experience with|hands-on|proficiency)\b"
)

# Qualifiers that cap the level no matter which verb appears (guide, Step 3).
_AWARE_CAP = (
    r"\b(completed (an? |the )?[\w\s-]{0,40}?(course|training|module)|course module|"
    r"read about|read the|studied|currently learning|familiar with|familiarity with|"
    r"exposure to|introduced to|attended|listed as a topic|while preparing)\b"
)
_USED_CAP = r"\b(contributed to|assisted|helped|participated in|joined|reviewed|shadowed|supported the)\b"

# Requirement wording (guide, Step 2).
_REQ_AWARE = r"^\s*(familiarity|familiar|exposure|understanding|knowledge|awareness)\b"
_REQ_OWNED = r"\b(lead|own|drive|architect|responsible for|mentor|manage)\b"
_REQ_BUILT = r"\b(build|design|develop|implement|deploy|write|automate|set up|create|maintain)\b"


def _has(pattern: str, text: str) -> bool:
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def evidence_level(text: str) -> Level:
    """Strength of what the candidate personally did in one evidence item."""
    if _has(_OWNED, text):
        level = Level.OWNED
    elif _has(_BUILT, text):
        level = Level.BUILT
    elif _has(_USED, text):
        level = Level.USED
    else:
        # A bare skill mention ("Python, SQL, Docker") shows awareness at most.
        level = Level.AWARE

    # Qualifiers set the level outright: "contributed to the deployment" is
    # participation (L2) whatever verb or noun follows it.
    if _has(_AWARE_CAP, text):
        return Level.AWARE
    if _has(_USED_CAP, text):
        return Level.USED
    return level


def required_level(text: str) -> Level:
    """Strength a requirement asks for, read from its wording."""
    if _has(_REQ_AWARE, text):
        return Level.AWARE
    if _has(_REQ_OWNED, text):
        return Level.OWNED
    if _has(_REQ_BUILT, text):
        return Level.BUILT
    return Level.USED


LEVEL_WORDS = {
    Level.NONE: "no direct involvement",
    Level.AWARE: "awareness",
    Level.USED: "use",
    Level.BUILT: "building",
    Level.OWNED: "ownership",
}

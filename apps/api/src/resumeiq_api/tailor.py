"""Tailor plan: turn a fit map into concrete, ordered steps for this job.

Every action is derived from what the matcher already knows (requirement
components, evidence levels, exact offsets), so it works for any posting and any
resume rather than a fixed list of cases:

* a component nobody mentions                    -> MISSING
* named only in a skills list                    -> LISTED_NOT_SHOWN
* only studied (course, reading)                 -> LEARNED_NOT_USED
* shown, but weaker than asked ("contributed")   -> BELOW_LEVEL
* some components shown, others not             -> PARTIAL_COVERAGE
* same skill, different name from the posting    -> WORDING
* backed, but the line has no measurable result  -> ADD_RESULT

Actions never contain invented facts. Suggestions are shapes with [placeholders]
the user must fill truthfully, and no action ever tells someone to claim more
than their evidence shows.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from .levels import LEVEL_WORDS
from .matching import _cite
from .matching_v2 import read_requirement
from .models import Action, ActionKind, Coverage, EvidenceItem, Level, RequirementResult, SourceDocument
from .rewrite import EvidenceLine, rule_based_shape
from .terms import content_terms, tokens

# Same skill, different names. The posting's own form is the one to use. Short,
# ambiguous forms ("ML", "JS") only match in capitals so "html" never counts.
WORDING_GROUPS: list[list[str]] = [
    ["PostgreSQL", "Postgres"],
    ["Kubernetes", "K8s"],
    ["scikit-learn", "sklearn", "scikit learn"],
    ["JavaScript", "JS"],
    ["Node.js", "NodeJS"],
    ["React", "ReactJS", "React.js"],
    ["Next.js", "NextJS"],
    ["Vue", "Vue.js", "VueJS"],
    ["GCP", "Google Cloud Platform", "Google Cloud"],
    ["AWS", "Amazon Web Services"],
    ["CI/CD", "CICD", "continuous integration"],
    ["machine learning", "ML"],
    ["natural language processing", "NLP"],
    ["large language models", "LLMs", "large language model", "LLM"],
    ["Power BI", "PowerBI"],
    ["SQL Server", "MS SQL", "MSSQL"],
    ["REST APIs", "RESTful APIs", "REST API", "RESTful API"],
    ["Hugging Face", "HuggingFace"],
    ["A/B testing", "A/B tests", "split testing"],
    ["ETL", "extract, transform, load"],
    ["TensorFlow", "Tensorflow"],
    ["PyTorch", "Pytorch"],
    ["GitHub Actions", "GH Actions"],
]

# A result is a measured change, not just a count ("14 stores" is scale).
_RESULT = [
    re.compile(r"\b\d+(?:\.\d+)?\s?%"),
    re.compile(r"\$\s?\d"),
    re.compile(r"\b\d+(?:\.\d+)?x\b", re.I),
    re.compile(
        r"\b(?:reduc|increas|improv|cut|sav|grew|grow|rais|lower|boost|shorten|speed)\w*\b[^.]*\b(?:by|from|to)\s+\d",
        re.I,
    ),
    re.compile(r"\bfrom\s+\d[^.]*\bto\s+\d", re.I),
]
_LIST_LIKE = re.compile(r"^\s*(?:technical\s+)?skills?\s*[:\-]", re.I)
_CLAIM_HINT = {
    Level.OWNED: "led or owned",
    Level.BUILT: "built or designed",
    Level.USED: "used",
    Level.AWARE: "learned",
}


def has_result(text: str) -> bool:
    return any(p.search(text) for p in _RESULT)


def _is_list_like(text: str) -> bool:
    """A skills line: "Skills: Python, SQL, Docker" or a bare comma list of short items."""
    if _LIST_LIKE.search(text):
        return True
    parts = [p.strip() for p in text.split(",")]
    return len(parts) >= 3 and sum(len(p.split()) for p in parts) / len(parts) <= 3


def _label(requirement: str, unit: frozenset[str]) -> str:
    """Readable name for a component, in the requirement's own words."""
    words = []
    for word in re.findall(r"[\w+#.\-/]+", requirement):
        if set(tokens(word)) & unit:
            words.append(word.strip(".,;:"))
    return " or ".join(dict.fromkeys(words)) or sorted(unit)[0]


def _covers(item: EvidenceItem, unit: frozenset[str]) -> bool:
    return bool(unit & content_terms(item.text))


def _form_pattern(form: str) -> re.Pattern[str]:
    flags = 0 if len(form) <= 4 and form.isupper() else re.I
    return re.compile(rf"(?<![\w.]){re.escape(form)}(?![\w])", flags)


def wording_mismatches(job_text: str, resume_text: str) -> list[tuple[str, str]]:
    """(posting form, resume form) pairs where the resume names the skill differently."""
    found = []
    for group in WORDING_GROUPS:
        in_job = [f for f in group if _form_pattern(f).search(job_text)]
        in_resume = [f for f in group if _form_pattern(f).search(resume_text)]
        if in_job and in_resume and not set(in_job) & set(in_resume):
            found.append((in_job[0], in_resume[0]))
    return found


def build_actions(
    results: Sequence[RequirementResult],
    evidence: Sequence[EvidenceItem],
    documents: Sequence[SourceDocument],
    job_text: str,
) -> list[Action]:
    by_id = {item.id: item for item in evidence}
    resume_ids = {d.id for d in documents if d.kind == "resume"}
    raw: list[tuple[int, int, Action]] = []  # (priority, requirement order, action)
    result_lines_seen: set[str] = set()

    def add(order: int, **fields) -> None:
        raw.append((fields["priority"], order, Action(id="", **fields)))

    for order, result in enumerate(results):
        req = result.requirement
        must = req.priority == "must"
        _, units = read_requirement(req.text)
        if not units:
            continue
        need = LEVEL_WORDS[req.required_level]
        cited = [by_id[c.evidence_id] for c in result.citations if c.evidence_id in by_id]

        if result.status is Coverage.SUPPORTED:
            for item in cited:
                if (
                    must
                    and item.document_id in resume_ids
                    and item.id not in result_lines_seen
                    and not has_result(item.text)
                    and not _is_list_like(item.text)  # a skills list is not a bullet to add results to
                ):
                    result_lines_seen.add(item.id)
                    add(
                        order,
                        kind=ActionKind.ADD_RESULT,
                        priority=3,
                        requirement_id=req.id,
                        title="Add a result to a line that backs a must-have",
                        detail=(
                            f"This line backs “{req.text}”. It says what you did, not what changed. "
                            "Add a measurable result if you have one: time saved, errors reduced, users served, cost."
                        ),
                        citations=[_cite(item, 1.0)],
                        suggestion=f"{item.text.rstrip('. ')}, [add measurable result].",
                    )
            continue

        if result.status is Coverage.PARTIAL:
            strongest = max((c.level for c in result.citations), default=Level.NONE)
            if strongest < req.required_level:
                lines = [EvidenceLine(c.evidence_id, c.quote) for c in result.citations]
                add(
                    order,
                    kind=ActionKind.BELOW_LEVEL,
                    priority=1 if must else 2,
                    requirement_id=req.id,
                    title=f"Stronger evidence needed: {req.text}",
                    detail=(
                        f"Your strongest line shows {LEVEL_WORDS[strongest]}; the job asks for {need}. "
                        f"If you {_CLAIM_HINT.get(req.required_level, 'did')} any part of it, say exactly which part. "
                        "If you did not, leave the line as it is: an overstated claim is easy to spot in an interview."
                    ),
                    citations=result.citations,
                    suggestion=rule_based_shape(lines) + "." if lines else None,
                )
            covered = [u for u in units if any(_covers(i, u) for i in cited)]
            missing = [u for u in units if u not in covered]
            if covered and missing:
                found_l = ", ".join(_label(req.text, u) for u in covered)
                missing_l = ", ".join(_label(req.text, u) for u in missing)
                add(
                    order,
                    kind=ActionKind.PARTIAL_COVERAGE,
                    priority=1 if must else 2,
                    requirement_id=req.id,
                    title=f"Partly shown: {req.text}",
                    detail=(
                        f"Your evidence shows {found_l} but not {missing_l}. "
                        f"If you have worked with {missing_l}, add it to that line or write a new bullet."
                    ),
                    terms=[_label(req.text, u) for u in missing],
                    citations=result.citations,
                    suggestion=f"[Action verb] [what you did] with {missing_l}, [add measurable result].",
                )
            continue

        # Not found: is the skill mentioned somewhere weaker, or nowhere at all?
        mentions = [i for i in evidence if any(_covers(i, u) for u in units)]
        mention_cover = [u for u in units if any(_covers(i, u) for i in mentions)]
        label_all = ", ".join(_label(req.text, u) for u in units)
        if mentions and len(mention_cover) / len(units) >= 0.5:
            best = sorted(mentions, key=lambda i: (-sum(_covers(i, u) for u in units), -int(i.level)))[:2]
            listed = any(_is_list_like(i.text) for i in best)
            weak = max(i.level for i in best) <= Level.AWARE
            if weak:
                kind = ActionKind.LISTED_NOT_SHOWN if listed else ActionKind.LEARNED_NOT_USED
                labels = ", ".join(_label(req.text, u) for u in mention_cover)
                if kind is ActionKind.LISTED_NOT_SHOWN:
                    title = f"Listed, but not shown: {labels}"
                    detail = (
                        f"{labels} appears in your skills list, but no bullet shows you using it, and the job asks "
                        f"for {need}. Add one line that says where you used it and what came of it."
                    )
                else:
                    title = f"Learned, not yet used: {labels}"
                    detail = (
                        f"You have studied {labels}, but no line shows you using it, and the job asks for {need}. "
                        "If you have used it since, say where. If not, keep it under Education or Certifications "
                        "and call it learning, not experience."
                    )
                add(
                    order,
                    kind=kind,
                    priority=1 if must else 2,
                    requirement_id=req.id,
                    title=title,
                    detail=detail,
                    terms=[_label(req.text, u) for u in mention_cover],
                    citations=[_cite(i, 1.0) for i in best],
                    suggestion=f"[Action verb] [what you built or did] with {labels}, [add measurable result].",
                )
                continue
            # Real experience that the matcher judged too thin for this requirement.
            missing = [u for u in units if u not in mention_cover]
            if missing:
                found_l = ", ".join(_label(req.text, u) for u in mention_cover)
                missing_l = ", ".join(_label(req.text, u) for u in missing)
                add(
                    order,
                    kind=ActionKind.PARTIAL_COVERAGE,
                    priority=1 if must else 2,
                    requirement_id=req.id,
                    title=f"Partly shown: {req.text}",
                    detail=(
                        f"Your documents show {found_l} but not {missing_l}. "
                        f"If you have worked with {missing_l}, add it to a bullet."
                    ),
                    terms=[_label(req.text, u) for u in missing],
                    citations=[_cite(i, 1.0) for i in best],
                    suggestion=f"[Action verb] [what you did] with {missing_l}, [add measurable result].",
                )
                continue

        add(
            order,
            kind=ActionKind.MISSING,
            priority=1 if must else 3,
            requirement_id=req.id,
            title=f"Not on your resume: {req.text}",
            detail=(
                f"Nothing in your documents mentions {label_all}. If you have done this, add a bullet that shows "
                "where and how. If you have not, treat it as a real gap for this role: do not add it, and point to "
                "the closest related experience in your cover letter instead."
                if must
                else f"Nice to have. Nothing mentions {label_all}. If you have done it, one line is enough; "
                "if not, it will not block you."
            ),
            terms=[_label(req.text, u) for u in units],
            suggestion=f"[Action verb] [what you did] with {label_all}, [add measurable result].",
        )

    resume_text = "\n".join(d.text for d in documents if d.kind == "resume")
    for posting_form, resume_form in wording_mismatches(job_text, resume_text):
        pattern = _form_pattern(resume_form)
        lines = [i for i in evidence if i.document_id in resume_ids and pattern.search(i.text)][:1]
        add(
            len(results),
            kind=ActionKind.WORDING,
            priority=2,
            title=f"Use the posting's wording: {posting_form}",
            detail=(
                f"The posting says “{posting_form}”; your resume says “{resume_form}”. It is the same "
                f"skill, but keyword filters often match exact words. Write “{posting_form}”, or "
                f"“{posting_form} ({resume_form})”."
            ),
            terms=[posting_form, resume_form],
            citations=[_cite(i, 1.0) for i in lines],
        )

    ordered = [a for _, _, a in sorted(raw, key=lambda t: (t[0], t[1]))]
    return [a.model_copy(update={"id": f"A{n + 1:02d}"}) for n, a in enumerate(ordered)]

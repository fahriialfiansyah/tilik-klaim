"""The gate. Every check must hold or the whole answer is rejected — nothing is trimmed.

ADR-0007 § 4.4: ADR-0005's five gates, plus the one this page adds — a citation on every
statement — and an English lexicon beside the Indonesian one, because this page answers in the
reader's language and an accusation is no less one in English.

The Indonesian lexicon is the briefing's own, imported rather than copied: two lists of what the
system may not say would be two lists that drift.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from tilik_domain.reasons import CaseState, PriorityBand, ReasonCode, RiskMode

from app.dto.assistant import AnswerKind, AssistantAnswer, CitationKind
from app.service.briefing.validation import ACCUSATORY, DIRECTIVE, Verdict

ENGLISH_ACCUSATORY: tuple[str, ...] = (
    r"\bfraud\w*",
    r"\bfalsif\w*",
    r"\b(fake|faked|forged|forgery)\b",
    r"\b(cheat\w*|scam\w*|dishonest\w*)\b",
    r"\b(sanction\w*|penalt\w*)\b",
    # Certainty and reassurance, standalone. Negated forms are masked first — see `_NEGATED`.
    r"\bproven\b",
    r"\bguilty\b",
    r"\bclean\b",
    r"\bsafe\b",
    r"\b(misconduct|illegal\w*|abus(e|ed|ive)|suspicious\w*)\b",
)

INDONESIAN_EXTRA: tuple[str, ...] = (
    # Beyond the briefing's lexicon: wrongdoing and suspicion, which an assistant asked open
    # questions is likelier to reach for than a fixed summary is.
    r"\bmencurigakan\b",
    r"\bilegal\b",
    r"\bpenyalahgunaan\b",
    r"\bmelanggar\s+hukum\b",
)

ENGLISH_DIRECTIVE: tuple[str, ...] = (
    r"\b(should|must|need\s+to|ought\s+to)\s+(be\s+)?(reject|deny|denied|withh[eo]ld|refus|pa(y|id)|approv)\w*",
    r"\b(reject|deny|withhold|stop|refuse)\s+(the\s+|this\s+)?(claim|payment)\b",
    r"\bclaim\s+(is\s+|was\s+|should\s+be\s+)?(rejected|denied)\b",
)

FORBIDDEN_PATTERNS: tuple[str, ...] = (
    ACCUSATORY + DIRECTIVE + INDONESIAN_EXTRA + ENGLISH_ACCUSATORY + ENGLISH_DIRECTIVE
)

_FORBIDDEN = tuple((pattern, re.compile(pattern, re.IGNORECASE)) for pattern in FORBIDDEN_PATTERNS)

_NEGATED = re.compile(
    r"\b(tidak|belum|bukan|kurang|tanpa)\s+(dapat\s+|bisa\s+)?(pasti|terbukti|aman|bersih)\b"
    r"|\b(not|never|no\s+longer)\s+(yet\s+)?(be\s+)?(proven|clean|safe)\b"
    r"|\bunproven\b",
    re.IGNORECASE,
)
"""A negated certainty word is a hedge, and hedging is what this page is asked to do."""

_NUMBER = re.compile(r"\d+(?:[.,]\d+)*")

_IDENTIFIER = re.compile(r"\b(?:case_[0-9a-f]{4,}…?|[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+)")
"""An id-shaped token — `case_…`, or upper-case segments joined by hyphens — is never a word.

Resource ids are written into answers on purpose — `ENC-CLEAN-1`, `DOC-CL-2` — and a lexicon
reading `ENC-CLEAN-1` as the word "clean" rejects a correct answer for citing its own source.
Only that shape is masked, deliberately: masking every token with a digit let "fraud2" through.
"""


_MACHINE_TOKEN = re.compile(
    r"\b("
    + "|".join(
        sorted(
            {str(code) for enum in (PriorityBand, CaseState, RiskMode, ReasonCode) for code in enum},
            key=len,
            reverse=True,
        )
    )
    + r")\b"
)
"""Every band, state, pattern and reason code. None of them belongs in a sentence a reviewer reads.

The owner's rule (6 Sep 2026): raw machine tokens never appear on the reading surface. Measured
2 Oct 2026, the model wrote "band DETERMINISTIC_CONFLICT" into its prose; the labels it is now
given make that unlikely, and this makes it impossible to ship.
"""


def machine_token(text: str) -> str | None:
    found = _MACHINE_TOKEN.search(text)
    return found.group(0) if found else None


@dataclass(frozen=True)
class Citable:
    """Everything this turn may point at. Built from what was read, never from what was asked."""

    case_ids: frozenset[str]
    resources: frozenset[tuple[str, str, str]]
    """`(case_id, resource_type, resource_id)` for every resource of every case read this turn."""
    queue_allowed: bool


def _canonical(number: str) -> str:
    """One spelling per value: `01` is `1`, Indonesian `144,04` is `144.04`, `1.250.000` is
    `1250000`, `630000.00` is `630000`. A single separator is read as a decimal point — the safe
    reading, since a misread thousands group can only make a supported number look unsupported.
    """
    text = number.replace(",", ".")
    if text.count(".") > 1:
        text = text.replace(".", "")
    try:
        return format(Decimal(text).normalize(), "f")
    except InvalidOperation:
        return number


def _numbers(text: str) -> list[str]:
    """Numbers as written, with every id masked first — the digits in `case_c459a18…` or
    `ENC-PH-1` are part of a name, not a count."""
    return _NUMBER.findall(_IDENTIFIER.sub(" ", text))


def forbidden_term(text: str) -> str | None:
    """The first accusation or directive in `text`, as written — or `None`."""
    masked = _NEGATED.sub("«hedge»", _IDENTIFIER.sub("«id»", text))
    for pattern, matcher in _FORBIDDEN:
        found = matcher.search(masked)
        if found:
            return f"{found.group(0)!r} ({pattern})"
    return None


def _unresolved(answer: AssistantAnswer, citable: Citable) -> list[str]:
    bad = []
    for statement in answer.statements:
        for citation in statement.citations:
            if citation.kind is CitationKind.QUEUE and not citable.queue_allowed:
                bad.append("queue")
            elif citation.kind is CitationKind.CASE and citation.case_id not in citable.case_ids:
                bad.append(f"case {citation.case_id}")
            elif citation.kind is CitationKind.RESOURCE:
                key = (
                    str(citation.case_id),
                    str(citation.resource_type),
                    str(citation.resource_id),
                )
                if key not in citable.resources:
                    bad.append(f"{citation.resource_type} {citation.resource_id}")
    for card in answer.cases:
        if card.case.case_id not in citable.case_ids:
            bad.append(f"card {card.case.case_id}")
    return bad


def validate_answer(answer: AssistantAnswer, citable: Citable, supplied_text: str) -> Verdict:
    """`supplied_text` is the tool output the model was shown this turn — never the question.

    A number the reviewer typed is not evidence: "is this a 500 million loss?" must not license
    "a 500 million loss" in the answer.
    """
    if answer.kind is not AnswerKind.ANSWER or not answer.statements:
        return Verdict(accepted=False, reason="a generated answer must be an ANSWER with statements")

    # 1. every statement cites something, and every citation resolves to what was read
    unresolved = _unresolved(answer, citable)
    if unresolved:
        return Verdict(accepted=False, reason=f"unresolved citation: {', '.join(unresolved)}")

    sentences = [statement.text for statement in answer.statements]

    # 2. every number was in the material supplied — as a whole number, not inside another one
    supplied_numbers = {_canonical(n) for n in _numbers(supplied_text)}
    for sentence in [*sentences, answer.uncertainty_note]:
        unsupported = [n for n in _numbers(sentence) if _canonical(n) not in supplied_numbers]
        if unsupported:
            return Verdict(accepted=False, reason=f"unsupported number: {', '.join(unsupported)}")

    # 3. no accusation and no directive, in either language
    found = forbidden_term(" ".join([*sentences, answer.uncertainty_note]))
    if found:
        return Verdict(accepted=False, reason=f"forbidden term {found}")

    # 4. no raw machine token on the reading surface
    token = machine_token(" ".join([*sentences, answer.uncertainty_note]))
    if token:
        return Verdict(accepted=False, reason=f"machine token {token!r}")

    # 5. caps are enforced by the schema; 6. the note must say something
    if not answer.uncertainty_note.strip():
        return Verdict(accepted=False, reason="empty uncertainty note")
    return Verdict(accepted=True)

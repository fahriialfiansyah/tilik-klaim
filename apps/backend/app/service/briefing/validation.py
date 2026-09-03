"""The gate. All five must hold or the whole briefing is rejected — nothing is trimmed.

`05_model_card.md` § Optional LLM guardrails, made executable: "reject output containing
unsupported resource IDs or numbers" and "never use 'fraud' as a finding".
"""
from __future__ import annotations

import re

from app.dto.briefing import CaseBriefing
from app.dto.cases import CaseDetailResponse
from app.dto.common import Dto, EvidenceRefDto

FORBIDDEN_TERMS: tuple[str, ...] = (
    # the rules' own lexicon
    "fraud", "curang", "palsu", "tolak", "sanksi",
    # certainty or safety the system is not entitled to assert
    "terbukti", "pasti", "bersih", "aman",
    # payment
    "bayar", "denda",
)

_NUMBER = re.compile(r"\d+(?:[.,]\d+)*")


class Verdict(Dto):
    accepted: bool
    reason: str | None = None


def _unresolved(refs: tuple[EvidenceRefDto, ...], detail: CaseDetailResponse) -> list[str]:
    known = {(str(s.resource_type), s.resource_id) for s in detail.sources}
    return [
        f"{ref.resource_type} {ref.resource_id}"
        for ref in refs
        if (str(ref.resource_type), ref.resource_id) not in known
    ]


def _unsupported_numbers(text: str, supplied_text: str) -> list[str]:
    return [number for number in _NUMBER.findall(text) if number not in supplied_text]


def validate_briefing(
    briefing: CaseBriefing, detail: CaseDetailResponse, supplied_text: str
) -> Verdict:
    """`supplied_text` is everything the model was shown — tool output, verbatim."""
    sentences = [o.statement for o in briefing.observations]
    sentences += [q.question for q in briefing.open_questions]
    sentences += [q.why_it_matters for q in briefing.open_questions]

    # 1. every reference resolves in this case's own source index
    for item in (*briefing.observations, *briefing.open_questions):
        unresolved = _unresolved(item.source_refs, detail)
        if unresolved:
            return Verdict(accepted=False, reason=f"unresolved reference: {', '.join(unresolved)}")

    # 2. every number was in the material supplied
    for sentence in sentences:
        bad = _unsupported_numbers(sentence, supplied_text)
        if bad:
            return Verdict(accepted=False, reason=f"unsupported number: {', '.join(bad)}")

    # 3. no forbidden term
    lowered = " ".join([*sentences, briefing.uncertainty_note]).lower()
    for word in FORBIDDEN_TERMS:
        if word in lowered:
            return Verdict(accepted=False, reason=f"forbidden term: {word}")

    # 4. caps and lengths are enforced by the schema; 5. the note must say something
    if not briefing.uncertainty_note.strip():
        return Verdict(accepted=False, reason="empty uncertainty note")
    return Verdict(accepted=True)

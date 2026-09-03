"""The gate. All five must hold or the whole briefing is rejected — nothing is trimmed.

`05_model_card.md` § Optional LLM guardrails, made executable: "reject output containing
unsupported resource IDs or numbers" and "never use 'fraud' as a finding".
"""
from __future__ import annotations

import re

from app.dto.briefing import CaseBriefing
from app.dto.cases import CaseDetailResponse
from app.dto.common import Dto, EvidenceRefDto

# Two lists, because two different things are forbidden and a substring match cannot tell them
# apart. Indonesian attaches affixes directly to the stem, so a bare `in` test on "bayar" also
# rejects "pembayaran", on "aman" also rejects "keamanan", and on "pasti" also rejects
# "memastikan" — ordinary words a factual briefing needs. Measured against the gateway: that
# blunt rule rejected legitimate output on the repeat-billing and unbundling cases, the two
# modes where billing vocabulary is unavoidable, and silently degraded them to the template.
#
# What the canon actually forbids is an **accusation** and a **directive** — not the noun.

ACCUSATORY: tuple[str, ...] = (
    # Any form of these is an accusation or an unwarranted certainty. Affixes included on
    # purpose: "kecurangan" and "pemalsuan" are exactly as forbidden as their stems.
    r"fraud",
    r"\w*curang\w*",
    # Nasal mutation: "pemalsuan" is pe+malsu+an, so the p-stem alone misses it.
    r"\w*(palsu|malsu)\w*",
    r"sanksi",
    r"\w*denda\w*",
    # Standalone only: the certainty sense is forbidden, the ordinary verb is not.
    # `\bpasti\b` rejects "pasti" and leaves "memastikan"; `\baman\b` leaves "keamanan".
    # Negated forms are masked out before this runs — see `_NEGATED`.
    r"\bterbukti\b",
    r"\bpasti\b",
    r"\bbersih\b",
    r"\baman\b",
)

_NEGATED = re.compile(
    r"\b(tidak|belum|bukan|kurang|tanpa)\s+(dapat\s+|bisa\s+)?(pasti|terbukti|aman|bersih)\b",
    re.IGNORECASE,
)
"""A negated certainty word is a **hedge**, and hedging is what this briefing is asked to do.

Measured against the gateway: banning the bare word rejected "tidak pasti" and "belum terbukti"
— the model expressing uncertainty correctly — and pushed good output to the template. The
prohibition is on *asserting* certainty, so the negated forms are masked before the check.
"""

DIRECTIVE: tuple[str, ...] = (
    # Telling anyone to move, withhold, or refuse money — or to reject the claim.
    r"(harus|wajib|jangan|tidak boleh|sebaiknya|agar)\s+di(bayar|tolak)\w*",
    r"(hentikan|tolak|batalkan|setop|tahan)\s+pembayaran",
    r"klaim\s+\w*\s*ditolak",
    r"menolak\s+klaim",
    r"tolak\s+(sinyal|klaim)",
)

FORBIDDEN_PATTERNS: tuple[str, ...] = ACCUSATORY + DIRECTIVE

FORBIDDEN_TERMS = FORBIDDEN_PATTERNS
"""Kept as an alias: the template test parametrises over it."""

_FORBIDDEN = tuple((pattern, re.compile(pattern, re.IGNORECASE)) for pattern in FORBIDDEN_PATTERNS)

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

    # 3. no accusation and no directive
    joined = _NEGATED.sub("«hedge»", " ".join([*sentences, briefing.uncertainty_note]))
    for pattern, matcher in _FORBIDDEN:
        found = matcher.search(joined)
        if found:
            # Report what was written, not only the rule it broke — the rule alone sent one
            # debugging session looking in the wrong place.
            return Verdict(accepted=False, reason=f"forbidden term {found.group(0)!r} ({pattern})")

    # 4. caps and lengths are enforced by the schema; 5. the note must say something
    if not briefing.uncertainty_note.strip():
        return Verdict(accepted=False, reason="empty uncertainty note")
    return Verdict(accepted=True)

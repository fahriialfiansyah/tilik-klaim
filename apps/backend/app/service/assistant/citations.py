"""Citations and case cards — the only things an answer can point at.

Built here, from objects the turn actually read, so a citation is a reference that already
opens rather than one checked afterwards. Labels are a courtesy for copy-paste and screen
readers; the client resolves what a citation opens from its kind and ids, never from its label.
"""
from __future__ import annotations

from tilik_domain.locale import Locale

from app.dto.assistant import CaseCard, Citation, CitationKind
from app.dto.cases import CaseSummary
from app.dto.common import EvidenceRefDto
from app.service.assistant.wording import pick, resource_label

SHORT_ID_CHARS = 12
"""Long identifiers are shown as a 12-character prefix and an ellipsis — the UI's own rule."""


def short_id(case_id: str) -> str:
    return case_id if len(case_id) <= SHORT_ID_CHARS + 1 else f"{case_id[:SHORT_ID_CHARS]}…"


def queue_citation(locale: Locale) -> Citation:
    return Citation(kind=CitationKind.QUEUE, label=pick(locale, "Antrean Review", "Review Queue"))


def case_citation(case_id: str, locale: Locale) -> Citation:
    return Citation(
        kind=CitationKind.CASE,
        case_id=case_id,
        label=pick(locale, f"Kasus {short_id(case_id)}", f"Case {short_id(case_id)}"),
    )


def resource_citation(case_id: str, ref: EvidenceRefDto, locale: Locale) -> Citation:
    return Citation(
        kind=CitationKind.RESOURCE,
        case_id=case_id,
        resource_type=ref.resource_type,
        resource_id=ref.resource_id,
        label=f"{resource_label(ref.resource_type, locale)} {ref.resource_id}",
    )


def card(row: CaseSummary, position: int) -> CaseCard:
    return CaseCard(queue_position=position, case=row)

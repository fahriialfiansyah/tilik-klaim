"""The deterministic briefing — the default, and what ships if the LLM is ever killed.

Pure functions over the detail response. Every sentence is catalog text or a template over it,
so it is `test_no_rule_ever_uses_the_word_fraud`-safe by construction, and every observation
carries the refs of the reason it describes. `08_demo_runbook.md`: "Never depend on a remote
LLM" — this is the path the offline demo runs.
"""
from __future__ import annotations

from tilik_domain.versioning import EngineIdentity

from app.dto.briefing import (
    MAX_OBSERVATIONS,
    MAX_QUESTIONS,
    BriefingObservation,
    BriefingQuestion,
    CaseBriefing,
    Confidence,
    GeneratedBy,
    ObservationKind,
)
from app.dto.cases import CaseDetailResponse
from app.dto.common import EvidenceRefDto, ReasonDto, VersionStamp
from app.service.briefing.labels import resource_label

PROMPT_VERSION = "template-1"

UNCERTAINTY_NOTE = (
    "Ringkasan ini disusun hanya dari bukti yang ikut terkirim dalam bundel. Ketiadaan catatan "
    "di sini bukan bukti bahwa layanan tidak diberikan. Ringkasan tidak mengubah pita, status, "
    "maupun keputusan peninjau."
)

QUIET_STATEMENT = (
    "Tidak ada risiko teramati pada versi mesin ini, sehingga tidak ada jenis bukti yang "
    "diharapkan untuk diperiksa. Ini bukan pernyataan tentang klaimnya."
)

_ELLIPSIS = "…"


def _clip(text: str, limit: int = 240) -> str:
    if len(text) <= limit:
        return text
    cut = text[: limit - 1].rsplit(" ", 1)[0]
    return cut + _ELLIPSIS


def _first_ref(detail: CaseDetailResponse) -> EvidenceRefDto | None:
    for reason in detail.reasons:
        if reason.evidence:
            return reason.evidence[0]
    for event in detail.timeline:
        if event.resource is not None:
            return event.resource
    return None


def _gap_observation(reason: ReasonDto) -> BriefingObservation | None:
    if not reason.evidence:
        return None
    found_types = {ref.resource_type for ref in reason.evidence}
    missing = [t for t in reason.expected_support if t not in found_types]
    found = [t for t in reason.expected_support if t in found_types]
    if missing:
        statement = (
            f"{reason.sentence} Diharapkan: {', '.join(resource_label(t) for t in reason.expected_support)}. "
            f"Tidak ditemukan di bundel: {', '.join(resource_label(t) for t in missing)}."
        )
        kind = ObservationKind.EVIDENCE_GAP
    else:
        statement = (
            f"{reason.sentence} Bukti yang dirujuk ditemukan: "
            f"{', '.join(resource_label(t) for t in found) or 'sesuai rujukan'}."
        )
        kind = ObservationKind.CORROBORATION
    return BriefingObservation(
        statement=_clip(statement),
        kind=kind,
        source_refs=reason.evidence,
        reason_code=reason.code,
        confidence=Confidence.STATED,
    )


def _counter_observations(reason: ReasonDto) -> list[BriefingObservation]:
    out = []
    for note in reason.counter_evidence_notes:
        refs = note.refs or reason.evidence
        if not refs:
            continue
        out.append(
            BriefingObservation(
                statement=_clip(note.note),
                kind=ObservationKind.COUNTER_EVIDENCE,
                source_refs=refs,
                reason_code=reason.code,
                confidence=Confidence.STATED,
            )
        )
    return out


def _completeness_observation(detail: CaseDetailResponse) -> BriefingObservation | None:
    c = detail.evidence_completeness
    ref = _first_ref(detail)
    if ref is None or (c.bundle_complete and c.missing_reference_count == 0):
        return None
    parts = []
    if not c.bundle_complete:
        parts.append("Bundel dinyatakan belum lengkap, sehingga baris tanpa bukti belum dapat dinilai.")
    if c.missing_reference_count > 0:
        parts.append(f"{c.missing_reference_count} rujukan bukti tidak dapat diselesaikan.")
    return BriefingObservation(
        statement=_clip(" ".join(parts)),
        kind=ObservationKind.COMPLETENESS,
        source_refs=(ref,),
        confidence=Confidence.STATED,
    )


def _questions(detail: CaseDetailResponse) -> tuple[BriefingQuestion, ...]:
    out: list[BriefingQuestion] = []
    for reason in detail.reasons:
        if not reason.evidence:
            continue
        found_types = {ref.resource_type for ref in reason.evidence}
        for missing in (t for t in reason.expected_support if t not in found_types):
            out.append(
                BriefingQuestion(
                    question=_clip(f"Apakah {resource_label(missing)} untuk alasan ini tersedia di sistem atau berkas lain?"),
                    why_it_matters="Membedakan bukti yang tidak ada dari bukti yang hanya tidak ikut terkirim.",
                    source_refs=reason.evidence,
                )
            )
            if len(out) == MAX_QUESTIONS:
                return tuple(out)
    return tuple(out)


def template_briefing(detail: CaseDetailResponse, identity: EngineIdentity) -> CaseBriefing:
    observations: list[BriefingObservation] = []
    if not detail.reasons:
        ref = _first_ref(detail)
        if ref is not None:
            observations.append(
                BriefingObservation(
                    statement=QUIET_STATEMENT,
                    kind=ObservationKind.COMPLETENESS,
                    source_refs=(ref,),
                    confidence=Confidence.STATED,
                )
            )
    # Gaps first — they are the finding — then completeness, then what argues against.
    for reason in detail.reasons:
        gap = _gap_observation(reason)
        if gap is not None:
            observations.append(gap)
    completeness = _completeness_observation(detail)
    if completeness is not None:
        observations.append(completeness)
    for reason in detail.reasons:
        observations.extend(_counter_observations(reason))

    return CaseBriefing(
        case_id=detail.case_id,
        case_version=detail.case_version,
        observations=tuple(observations[:MAX_OBSERVATIONS]),
        open_questions=_questions(detail),
        uncertainty_note=UNCERTAINTY_NOTE,
        generated_by=GeneratedBy.TEMPLATE,
        model_id=None,
        prompt_version=PROMPT_VERSION,
        versions=VersionStamp(**identity.model_dump()),
    )

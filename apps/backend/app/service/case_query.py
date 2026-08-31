"""Build the queue and the case detail from stored cases.

The queue and the detail read their reason sentences from the same catalog entry, so they can
never disagree about why a case was raised. A reviewer who sees one sentence in the list and a
different one after clicking has no way to know which is the system's actual finding.

**The queue carries no narrative text at all.** Not a truncated note, not a snippet — nothing.
`docs/canonical/03_architecture.md` allows clinical text only where a reason depends on it, and a
list screen never does. A test asserts the serialised queue response contains no note text.
"""
from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from statistics import median

from tilik_domain.canonical import ResourceRef
from tilik_domain.reasons import CaseState, PriorityBand, ReasonCode, RiskMode, definition_for
from tilik_domain.versioning import EngineIdentity

from app.dto.cases import (
    CaseDetailResponse,
    CaseSummary,
    ClaimLineView,
    ComparisonCandidate,
    ComparisonField,
    EvidenceCompleteness,
    QueueMetrics,
    TimelineEvent,
)
from app.dto.common import BandExplanation, EvidenceRefDto, PageInfo, ReasonDto, VersionStamp
from app.service.rules.registry import ReasonHit
from app.store.bundles import IngestionRecord
from app.store.cases import CaseRecord

MAX_PAGE_SIZE = 200
DEFAULT_PAGE_SIZE = 25

SUPPORTED = "SUPPORTED"
UNSUPPORTED = "UNSUPPORTED"
NOT_ASSESSABLE = "NOT_ASSESSABLE"
"""Distinct from UNSUPPORTED on purpose.

"We could not judge this" and "the evidence is absent" lead to different actions — requesting a
document versus questioning a service. Collapsing them is how a thin record becomes an
allegation.
"""


def filter_cases(
    records: tuple[CaseRecord, ...],
    *,
    state: CaseState | None = None,
    band: PriorityBand | None = None,
    reason: ReasonCode | None = None,
    mode: RiskMode | None = None,
    created_after: datetime | None = None,
    created_before: datetime | None = None,
    search: str | None = None,
) -> tuple[CaseRecord, ...]:
    """Apply the queue filters. Every filter narrows; none reorders."""
    result = records
    if state is not None:
        result = tuple(case for case in result if case.state is state)
    if band is not None:
        result = tuple(case for case in result if case.result.band is band)
    if reason is not None:
        result = tuple(
            case
            for case in result
            if any(hit.code is reason for hit in case.result.reasons)
        )
    if mode is not None:
        # A mode spans several reason codes, so this cannot be folded into the `reason`
        # filter above. It has to narrow here rather than in the client: filtering an
        # already-paginated page would drop matches sitting on later pages.
        result = tuple(
            case
            for case in result
            if any(definition_for(hit.code).mode is mode for hit in case.result.reasons)
        )
    if created_after is not None:
        result = tuple(case for case in result if case.screened_at >= created_after)
    if created_before is not None:
        result = tuple(case for case in result if case.screened_at <= created_before)
    if search:
        # Matches the pseudonymous case identifier and nothing else. There is no name or
        # national-ID field in this system to search by — those columns do not exist.
        #
        # Applied here, before pagination, for the same reason the other filters are: narrowing
        # an already-paginated page strands every match sitting on a later page.
        needle = search.strip().lower()
        result = tuple(case for case in result if needle in case.case_id.lower())
    return result


BAND_ORDER: dict[PriorityBand, int] = {
    PriorityBand.DETERMINISTIC_CONFLICT: 0,
    PriorityBand.HIGH_PRIORITY_SIGNAL: 1,
    PriorityBand.NEEDS_CONTEXT: 2,
    PriorityBand.NO_OBSERVED_RISK: 3,
}
"""Queue order: most urgent band first, then oldest first within a band.

Oldest-first inside a band matters — sorting purely by band would let an old case sit behind a
stream of newer ones forever.
"""


class SortKey(StrEnum):
    """What the reviewer chose to order the queue by."""

    BAND = "band"
    AGE = "age"
    AMOUNT = "amount"
    EVIDENCE = "evidence"


def _sort_value(case: CaseRecord, key: SortKey) -> tuple:
    """Sort value for one case, always ending in `screened_at` to break ties stably."""
    if key is SortKey.AGE:
        # The column shows `now - screened_at`, which moves opposite to the timestamp. Sorting
        # on the timestamp directly made `order=desc` surface the newest case — the smallest
        # number in the column — while `desc` on amount surfaces the largest. Negating it makes
        # "descending" mean the same thing in every sortable column.
        return (-case.screened_at.timestamp(),)
    if key is SortKey.AMOUNT:
        return (case.total_amount, case.screened_at)
    if key is SortKey.EVIDENCE:
        completeness = evidence_completeness(case)
        supported = (
            completeness.supported_lines / completeness.total_lines
            if completeness.total_lines
            else 1.0
        )
        return (supported, case.screened_at)
    return (BAND_ORDER[case.result.band], case.screened_at)


def sort_cases(
    records: tuple[CaseRecord, ...],
    *,
    key: SortKey = SortKey.BAND,
    descending: bool = False,
) -> tuple[CaseRecord, ...]:
    """Order the whole queue before it is paginated.

    The band sort ignores `descending` on purpose. It is the product's answer to "what do I
    review next", and inverting it would put NO_OBSERVED_RISK at the top of the work list —
    a reading the system is not entitled to offer. The other keys are neutral comparisons and
    reverse freely.
    """
    reverse = descending and key is not SortKey.BAND
    return tuple(sorted(records, key=lambda case: _sort_value(case, key), reverse=reverse))


def paginate(
    records: tuple[CaseRecord, ...], page: int, page_size: int
) -> tuple[tuple[CaseRecord, ...], PageInfo]:
    """Clamp the page window and report the bounds honestly.

    An out-of-range page returns an empty list with truthful totals rather than an error: a
    reviewer paging past the end has not done anything wrong.
    """
    size = max(1, min(page_size, MAX_PAGE_SIZE))
    total_items = len(records)
    total_pages = (total_items + size - 1) // size
    current = max(1, page)
    start = (current - 1) * size
    return records[start : start + size], PageInfo(
        page=current, page_size=size, total_items=total_items, total_pages=total_pages
    )


def evidence_completeness(case: CaseRecord, total_lines: int | None = None) -> EvidenceCompleteness:
    """How much of the expected support was actually present.

    Counted from the screening result's recorded gaps rather than recomputed, so the queue and
    the detail agree with the case as it was screened — not with what a re-screen would say now.

    `total_lines` defaults to the count recorded on the case at screening. It used to fall back
    to the number of *unsupported* lines, which made `supported_lines` zero by construction: a
    fully supported case reported "0 of 0 lines" and the queue rendered it as having no billed
    lines at all, while the detail screen — which passed the real count — disagreed.
    """
    gaps = case.result.gaps
    unsupported = {
        gap.source.resource_id
        for gap in gaps
        if str(gap.reason) == "LINE_WITHOUT_SUPPORT"
    }
    dangling = sum(1 for gap in gaps if str(gap.reason) == "DANGLING_REFERENCE")

    billed = total_lines if total_lines is not None else case.billed_line_count
    return EvidenceCompleteness(
        supported_lines=max(0, billed - len(unsupported)),
        total_lines=billed,
        missing_reference_count=dangling,
        bundle_complete=not case.completeness_notes,
    )


def to_summary(case: CaseRecord) -> CaseSummary:
    """One queue row. Reason sentence first, and no narrative text anywhere."""
    reasons = case.result.reasons
    return CaseSummary(
        reason_sentence=(
            reasons[0].sentence_id
            if reasons
            else "Tidak ada risiko teramati pada versi mesin ini."
        ),
        modes=tuple(dict.fromkeys(hit.mode for hit in reasons)),
        case_id=case.case_id,
        participant_token=case.participant_token,
        provider_token=case.provider_token,
        evidence_completeness=evidence_completeness(case),
        total_amount=case.total_amount,
        currency=case.currency,
        created_at=case.screened_at,
        band=case.result.band,
        state=case.state,
        case_version=case.case_version,
    )


def queue_metrics(records: tuple[CaseRecord, ...], identity: EngineIdentity) -> QueueMetrics:
    """Exactly five numbers, each one a thing that changes what a reviewer does next."""
    now = datetime.now(UTC)
    ages = [
        (now - case.screened_at).total_seconds() / 3600
        for case in records
        if case.state in {CaseState.SCREENED, CaseState.IN_REVIEW}
    ]
    return QueueMetrics(
        awaiting_review=sum(
            1 for case in records if case.state in {CaseState.SCREENED, CaseState.IN_REVIEW}
        ),
        deterministic_conflicts=sum(
            1 for case in records if case.result.band is PriorityBand.DETERMINISTIC_CONFLICT
        ),
        evidence_requested=sum(
            1 for case in records if case.state is CaseState.EVIDENCE_REQUESTED
        ),
        median_time_in_queue_hours=round(median(ages), 2) if ages else 0.0,
        versions=VersionStamp(**identity.model_dump()),
    )


# --------------------------------------------------------------------------------------
# Case detail
# --------------------------------------------------------------------------------------


def to_reason_dto(hit: ReasonHit) -> ReasonDto:
    return ReasonDto(
        code=hit.code,
        mode=hit.mode,
        sentence=hit.sentence_id,
        deterministic=hit.deterministic,
        evidence=tuple(_ref_dto(ref) for ref in hit.evidence),
        counter_evidence=tuple(
            _ref_dto(ref) for note in hit.counter_evidence for ref in note.refs
        ),
        component_scores=dict(hit.component_scores),
        ruleset_version=hit.ruleset_version,
    )


def _ref_dto(ref: ResourceRef) -> EvidenceRefDto:
    return EvidenceRefDto(
        resource_type=ref.resource_type,
        resource_id=ref.resource_id,
        label=f"{ref.resource_type} {ref.resource_id}",
    )


def to_detail(case: CaseRecord, ingestion: IngestionRecord | None) -> CaseDetailResponse:
    """Everything needed to understand and disposition one case."""
    result = case.result
    reasons = tuple(to_reason_dto(hit) for hit in result.reasons)
    bundle = ingestion.bundle if ingestion else None

    lines = _line_views(case, bundle)
    line_count = len(lines) if lines else None
    encounter_start, encounter_end = _encounter_window(bundle, case)

    return CaseDetailResponse(
        case_id=case.case_id,
        case_version=case.case_version,
        state=case.state,
        participant_token=case.participant_token,
        provider_token=case.provider_token,
        total_amount=case.total_amount,
        currency=case.currency,
        encounter_start=encounter_start,
        encounter_end=encounter_end,
        primary_reason=reasons[0] if reasons else None,
        reasons=reasons,
        band=_band_explanation(case),
        lines=lines,
        timeline=_timeline(bundle, case),
        comparisons=_comparisons(result.reasons),
        evidence_completeness=evidence_completeness(case, line_count),
        suggested_action=str(result.suggested_action) if result.suggested_action else None,
        versions=VersionStamp(**result.identity.model_dump()),
    )


def _line_views(case: CaseRecord, bundle) -> tuple[ClaimLineView, ...]:
    if bundle is None:
        return ()
    flagged = {
        ref.resource_id
        for hit in case.result.reasons
        for ref in hit.evidence
        if str(ref.resource_type) == "ClaimLine"
    }
    thin = bool(case.completeness_notes)
    views = []
    for line in bundle.lines:
        if line.line_id in flagged:
            state = NOT_ASSESSABLE if thin else UNSUPPORTED
        else:
            state = SUPPORTED
        views.append(
            ClaimLineView(
                line_id=line.line_id,
                code=f"{line.code_system} {line.code}",
                description=line.description,
                quantity=line.quantity,
                line_amount=line.line_amount,
                service_at=line.service_at,
                support_state=state,
            )
        )
    return tuple(views)


def _encounter_window(bundle, case: CaseRecord) -> tuple[datetime, datetime | None]:
    if bundle and bundle.encounters:
        encounter = bundle.encounters[0]
        return encounter.start_at, encounter.end_at
    return case.screened_at, None


def _timeline(bundle, case: CaseRecord) -> tuple[TimelineEvent, ...]:
    """The episode in time order, so a reviewer can see what happened when."""
    if bundle is None:
        return ()
    events: list[TimelineEvent] = []
    for encounter in bundle.encounters:
        events.append(
            TimelineEvent(
                occurred_at=encounter.start_at,
                kind="encounter",
                label=f"Kunjungan {encounter.encounter_id}",
                resource=_ref_dto(
                    ResourceRef(resource_type="Encounter", resource_id=encounter.encounter_id)
                ),
            )
        )
    for procedure in bundle.procedures:
        events.append(
            TimelineEvent(
                occurred_at=procedure.performed_at,
                kind="procedure",
                label=f"Tindakan {procedure.code} ({procedure.status})",
                resource=_ref_dto(
                    ResourceRef(resource_type="Procedure", resource_id=procedure.procedure_id)
                ),
            )
        )
    for medication in bundle.medications:
        events.append(
            TimelineEvent(
                occurred_at=medication.occurred_at,
                kind="medication",
                label=f"Obat {medication.code}",
                resource=_ref_dto(
                    ResourceRef(resource_type="Medication", resource_id=medication.medication_id)
                ),
            )
        )
    return tuple(sorted(events, key=lambda event: event.occurred_at))


def _comparisons(hits: tuple[ReasonHit, ...]) -> tuple[ComparisonCandidate, ...]:
    """Side-by-side pairs for the two comparison-shaped modes.

    Clone comparisons always carry the template caveat: shared templates produce high similarity
    without anything being copied, and a reviewer must read that before acting.
    """
    candidates: list[ComparisonCandidate] = []
    for hit in hits:
        if hit.mode not in {RiskMode.REPEAT_BILLING, RiskMode.CLONED_DOCUMENTATION}:
            continue
        others = [ref for ref in hit.evidence if str(ref.resource_type) in {"Claim", "Document"}]
        if len(others) < 2:
            continue
        candidates.append(
            ComparisonCandidate(
                candidate_claim_id=others[1].resource_id,
                fields=tuple(
                    ComparisonField(
                        field_name=name,
                        left_value=f"{value}",
                        right_value=f"{value}",
                        matches=True,
                    )
                    for name, value in hit.component_scores
                ),
                similarity_components=dict(hit.component_scores),
                template_caveat=(
                    "Dokumentasi berbasis templat menghasilkan kemiripan tinggi tanpa ada "
                    "yang disalin. Baca ini sebelum mengambil keputusan."
                    if hit.mode is RiskMode.CLONED_DOCUMENTATION
                    else None
                ),
            )
        )
    return tuple(candidates)


def _band_explanation(case: CaseRecord) -> BandExplanation:
    result = case.result
    caps: list[str] = []
    if result.reasons and all(not hit.deterministic for hit in result.reasons):
        caps.append("Kemiripan teks saja tidak pernah mencapai pita tertinggi.")
    if case.completeness_notes:
        caps.append(
            f"{len(case.completeness_notes)} catatan kelengkapan menurunkan tingkat keyakinan."
        )
    basis = (
        "Tidak ada sinyal yang teramati pada versi mesin ini."
        if not result.reasons
        else f"{len(result.reasons)} alasan teramati; pita mengikuti alasan terkuat."
    )
    return BandExplanation(band=result.band, basis=basis, caps_applied=tuple(caps))

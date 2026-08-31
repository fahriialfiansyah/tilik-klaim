"""`GET /v1/cases` and `GET /v1/cases/{id}`."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import Field
from tilik_domain.canonical import ResourceType
from tilik_domain.reasons import CaseState, PriorityBand, RiskMode

from app.dto.common import BandExplanation, Dto, EvidenceRefDto, PageInfo, ReasonDto, VersionStamp


class EvidenceCompleteness(Dto):
    """How much of the expected supporting evidence was actually present.

    Surfaced in the queue so a reviewer can tell a thin record from a suspicious one before
    opening the case.
    """

    supported_lines: int = Field(ge=0)
    total_lines: int = Field(ge=0)
    missing_reference_count: int = Field(ge=0)
    bundle_complete: bool


class CaseSummary(Dto):
    """One queue row.

    **Pseudonymous fields only, and no raw medical text** — that is a hard constraint from
    `docs/canonical/03_architecture.md`, asserted by `test_queue_response_carries_no_medical_text`.
    Narrative text appears only in the detail response, and then only the fragment a reason
    depends on.

    Field order mirrors the mandated column order: the sentence comes first.
    """

    reason_sentence: str = Field(description="Working language. The queue's first column.")
    modes: tuple[RiskMode, ...]
    case_id: str
    participant_token: str = Field(description="Pseudonymous. Never a real identifier.")
    provider_token: str
    evidence_completeness: EvidenceCompleteness
    total_amount: Decimal
    currency: str
    created_at: datetime
    band: PriorityBand
    state: CaseState
    case_version: int = Field(ge=1)


class QueueMetrics(Dto):
    """The five operational metrics above the queue. Exactly five.

    Anything that does not change what a reviewer does next is excluded by
    `docs/canonical/01_product_decision.md` § Main dashboard principles — no "fraud saved",
    no provider league tables, no national projections.
    """

    awaiting_review: int = Field(ge=0)
    deterministic_conflicts: int = Field(ge=0)
    evidence_requested: int = Field(ge=0)
    median_time_in_queue_hours: float = Field(ge=0)
    versions: VersionStamp


class CaseQueueResponse(Dto):
    metrics: QueueMetrics
    items: tuple[CaseSummary, ...]
    page: PageInfo


class ClaimLineView(Dto):
    """One billed line with its support state.

    `NOT_ASSESSABLE` is distinct from `UNSUPPORTED`: the first means the record was too thin
    to judge, the second means the evidence is genuinely absent. Conflating them is the
    difference between requesting a document and alleging a service never happened.
    """

    line_id: str
    code: str
    description: str
    quantity: Decimal
    line_amount: Decimal
    service_at: datetime
    support_state: str = Field(
        description="SUPPORTED | PARTIALLY_SUPPORTED | UNSUPPORTED | NOT_ASSESSABLE"
    )


class TimelineEvent(Dto):
    occurred_at: datetime
    kind: str
    label: str
    resource: EvidenceRefDto | None = None


class ComparisonField(Dto):
    field_name: str
    left_value: str
    right_value: str
    matches: bool


class ComparisonCandidate(Dto):
    """Side-by-side pair for repeat-billing and cloned-documentation reasons."""

    candidate_case_id: str | None = None
    candidate_claim_id: str
    fields: tuple[ComparisonField, ...]
    overlap_start: datetime | None = None
    overlap_end: datetime | None = None
    similarity_components: dict[str, float] = Field(default_factory=dict)
    template_caveat: str | None = Field(
        default=None,
        description=(
            "Present on clone reasons. Legitimate template-based documentation produces high "
            "similarity too, and the reviewer must read that before acting."
        ),
    )


class SourceAvailability(StrEnum):
    """Why a referenced resource can or cannot be shown in full.

    Four outcomes, and keeping them apart is the whole point. Collapsing them into a boolean
    would put a deliberate privacy boundary and a genuine integrity defect behind the same
    empty panel, and `sprint/00-app-spec.md` § 4 rule 4 makes the second one a defect the
    screen has to name.
    """

    PRESENT = "PRESENT"
    """Carried by this bundle. Shown in full."""

    RELATED_BUNDLE = "RELATED_BUNDLE"
    """Belongs to another submission the rule compared against.

    Openable, so the reviewer can confirm the compared thing exists and when — but reduced to
    non-identifying fields. Never another participant's narrative, never their token.
    """

    NOT_STORED = "NOT_STORED"
    """Referenced by identity and never stored as a resource: an episode, a practitioner.

    Not a defect. `ResourceType.is_stored_resource` is the same distinction, made once.
    """

    MISSING = "MISSING"
    """Cited by a reason and resolvable to nothing. **This is the defect.**"""


class SourceField(Dto):
    """One field of a raw resource. Ordered pairs, so two renderings stay comparable."""

    name: str
    value: str


class SourceResource(Dto):
    """The resource behind an evidence reference, so every reference opens.

    An unresolvable reference is recorded here with `MISSING` rather than dropped. Dropping it
    would render as a shorter list — indistinguishable from a reason that cited less — which is
    exactly how a broken evidence trail hides.
    """

    resource_type: ResourceType
    resource_id: str
    label: str
    availability: SourceAvailability
    fields: tuple[SourceField, ...] = ()


class CaseDetailResponse(Dto):
    """Everything needed to understand and disposition one case."""

    case_id: str
    case_version: int = Field(ge=1)
    state: CaseState
    participant_token: str
    provider_token: str
    total_amount: Decimal
    currency: str
    encounter_start: datetime
    encounter_end: datetime | None
    primary_reason: ReasonDto | None
    reasons: tuple[ReasonDto, ...]
    band: BandExplanation
    lines: tuple[ClaimLineView, ...]
    timeline: tuple[TimelineEvent, ...]
    comparisons: tuple[ComparisonCandidate, ...] = ()
    evidence_completeness: EvidenceCompleteness
    sources: tuple[SourceResource, ...] = ()
    """Every resource any reason references, resolved once so the UI never guesses."""
    suggested_action: str | None = Field(
        default=None,
        description=(
            "What the system would suggest, e.g. REQUEST_EVIDENCE when the bundle is thin. "
            "A suggestion only — the reviewer chooses, and must still supply a reason."
        ),
    )
    versions: VersionStamp

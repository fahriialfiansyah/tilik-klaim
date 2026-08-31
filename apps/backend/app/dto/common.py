"""Shared response pieces.

Two rules bind every DTO in this package:

* **Pseudonymous only.** No names, no NIK, no real participant identifiers.
* **Reason before score.** Response models put the working-language sentence ahead of any
  band or numeric component, so a client rendering fields in declaration order gets the
  intended emphasis for free.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from tilik_domain.canonical import ResourceType
from tilik_domain.reasons import PriorityBand, ReasonCode, RiskMode


class Dto(BaseModel):
    """Base for every wire model."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class VersionStamp(Dto):
    """Engine identity carried on every screening result and audit event."""

    schema_version: str
    ruleset_version: str
    engine_version: str
    dataset_version: str


class EvidenceRefDto(Dto):
    """A pointer the UI must be able to open.

    A reference that does not resolve is a defect, not an empty panel — see
    `docs/canonical/06_evaluation_plan.md` § Evidence-reference validity.
    """

    resource_type: ResourceType
    resource_id: str
    label: str = Field(description="Short working-language description of the resource.")


class CounterEvidenceDto(Dto):
    """One fact that argues against the reason it accompanies, **in words**.

    The refs alone were shipped for a while and it hollowed the feature out: a reviewer saw
    `Encounter ENC-PH-1` under a "counter-evidence" heading with nothing saying why it weakened
    anything. The sentence is the argument; the references are only where to look next.
    """

    note: str = Field(description="Working language, written by the rule that raised the reason.")
    refs: tuple[EvidenceRefDto, ...] = ()


class ReasonDto(Dto):
    """One reason, with its evidence and whatever argues against it.

    `counter_evidence` is a first-class field rather than a separate lookup: the reviewer must
    see what weakens a signal on the same screen as the signal itself.
    """

    code: ReasonCode
    mode: RiskMode
    sentence: str = Field(description="From the reason catalog. Clients never compose their own.")
    deterministic: bool
    evidence: tuple[EvidenceRefDto, ...]
    expected_support: tuple[ResourceType, ...] = ()
    """Resource types that should stand behind the billed line, from the reason catalog.

    The screen shows expected evidence beside found evidence, and the gap between them is what
    a reviewer is actually judging. Deriving the expectation in the client would put a second
    copy of the catalog there, free to drift from the one that raised the reason.

    Note this is the catalog's `expected_support`, not its `required_evidence`. The latter is
    what the *reason* needs to be well formed, and rendering it here reported "everything
    expected was found" on a phantom case — whose whole finding is that something is absent.
    """
    counter_evidence: tuple[EvidenceRefDto, ...] = ()
    counter_evidence_notes: tuple[CounterEvidenceDto, ...] = ()
    """The same counter-evidence with its sentences kept.

    `counter_evidence` stays as the flat reference list it has always been so no existing
    client breaks; this field is the one a reviewer actually reads.
    """
    component_scores: dict[str, float] = Field(
        default_factory=dict,
        description="Per-component scores, kept alongside the reason rather than collapsed.",
    )
    ruleset_version: str


class BandExplanation(Dto):
    """Answers 'why this band?' for the queue tooltip and the case header."""

    band: PriorityBand
    basis: str = Field(description="How the band was reached, in working language.")
    caps_applied: tuple[str, ...] = Field(
        default=(),
        description=(
            "Guards that limited the band, e.g. text similarity alone cannot reach the top "
            "band, or an incomplete bundle lowered certainty."
        ),
    )


class PageInfo(Dto):
    """Queue pagination. The full queue is never returned in one response."""

    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=200)
    total_items: int = Field(ge=0)
    total_pages: int = Field(ge=0)


class Timestamped(Dto):
    occurred_at: datetime

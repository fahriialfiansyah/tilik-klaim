"""Canonical model — the prototype's internal shape for a claim and its clinical evidence.

Covers the eleven domains in `docs/canonical/04_data_card.md` § Minimum required schema.

These field names are **the prototype's internal canonical model**. They map to published
SATUSEHAT FHIR resources; they do not claim to reproduce a production implementation.

Two invariants hold throughout:

* **Pseudonymous only.** No names, no NIK, no real participant identifiers — not in the
  model, not in the UI, not in logs.
* **Immutable.** Every model is frozen. Corrections produce a new object; nothing is edited
  in place. This is what makes the audit trail trustworthy.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from tilik_domain.versioning import SCHEMA_VERSION


class Frozen(BaseModel):
    """Base for every canonical entity. Frozen by construction."""

    model_config = ConfigDict(frozen=True, extra="forbid")


# --------------------------------------------------------------------------------------
# References and provenance
# --------------------------------------------------------------------------------------


class ResourceType(StrEnum):
    CLAIM = "Claim"
    CLAIM_LINE = "ClaimLine"
    ENCOUNTER = "Encounter"
    CONDITION = "Condition"
    PROCEDURE = "Procedure"
    MEDICATION = "Medication"
    DIAGNOSTIC = "Diagnostic"
    DOCUMENT = "Document"
    ACCOUNT = "Account"
    CHARGE_ITEM = "ChargeItem"
    INVOICE = "Invoice"
    EPISODE = "Episode"


class ResourceRef(Frozen):
    """A typed pointer to another canonical resource.

    Every reference must resolve. A reference that points at a resource which is not present
    is a defect, not an empty display — see `docs/canonical/06_evaluation_plan.md`
    § Evidence-reference validity.
    """

    resource_type: ResourceType
    resource_id: str

    def key(self) -> tuple[str, str]:
        return (str(self.resource_type), self.resource_id)


class SourceType(StrEnum):
    SYNTHETIC_GENERATOR = "synthetic_generator"
    UPLOADED_BUNDLE = "uploaded_bundle"
    GOLD_FIXTURE = "gold_fixture"


class Provenance(Frozen):
    """Domain 10 — traceability and tamper-aware audit."""

    resource_id: str
    resource_type: ResourceType
    source_type: SourceType
    last_updated_at: datetime
    bundle_hash: str | None = None
    schema_version: str = SCHEMA_VERSION


# --------------------------------------------------------------------------------------
# Status vocabularies
# --------------------------------------------------------------------------------------


class EventStatus(StrEnum):
    """Shared status vocabulary for clinical events.

    `ENTERED_IN_ERROR` is deliberately distinct from absence: an event marked entered-in-error
    is evidence that was retracted, which is not the same as evidence that was never recorded.
    The rule engine must be able to tell them apart and say which one it saw.
    """

    COMPLETED = "completed"
    IN_PROGRESS = "in-progress"
    NOT_DONE = "not-done"
    ENTERED_IN_ERROR = "entered-in-error"
    UNKNOWN = "unknown"


class EncounterStatus(StrEnum):
    PLANNED = "planned"
    IN_PROGRESS = "in-progress"
    FINISHED = "finished"
    CANCELLED = "cancelled"
    ENTERED_IN_ERROR = "entered-in-error"


class ClaimStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    CANCELLED = "cancelled"
    ENTERED_IN_ERROR = "entered-in-error"


class VerificationStatus(StrEnum):
    CONFIRMED = "confirmed"
    PROVISIONAL = "provisional"
    DIFFERENTIAL = "differential"
    REFUTED = "refuted"
    ENTERED_IN_ERROR = "entered-in-error"


class CareType(StrEnum):
    INPATIENT = "inpatient"
    OUTPATIENT = "outpatient"
    EMERGENCY = "emergency"


# --------------------------------------------------------------------------------------
# Domains 1-2 — claim header and claim lines
# --------------------------------------------------------------------------------------


class ClaimLine(Frozen):
    """Domain 2 — one billed item. The unit the whole product reasons about."""

    line_id: str
    claim_id: str
    code_system: str
    code: str
    description: str
    quantity: Decimal
    unit_price: Decimal
    line_amount: Decimal
    service_at: datetime
    charge_item_ref: ResourceRef | None = None
    supporting_refs: tuple[ResourceRef, ...] = ()


class ClaimHeader(Frozen):
    """Domain 1 — episode linkage, duplication, and queue display."""

    claim_id: str
    participant_id: str  # pseudonymous token, never a real identifier
    provider_id: str
    encounter_id: str
    episode_id: str | None = None
    care_type: CareType
    submitted_at: datetime
    status: ClaimStatus
    total_amount: Decimal
    currency: str = "IDR"


# --------------------------------------------------------------------------------------
# Domain 3 — encounter
# --------------------------------------------------------------------------------------


class Encounter(Frozen):
    """Domain 3 — episode boundary, overlap, and chronology."""

    encounter_id: str
    class_code: str
    status: EncounterStatus
    start_at: datetime
    end_at: datetime | None = None
    provider_id: str
    location_id: str | None = None
    participant_id: str


# --------------------------------------------------------------------------------------
# Domains 4-8 — clinical evidence
# --------------------------------------------------------------------------------------


class Condition(Frozen):
    """Domain 4 — context only.

    Never used to decide medical necessity. That is out of scope for the prototype and
    requires clinical expertise the team does not have.
    """

    condition_id: str
    code_system: str
    code: str
    recorded_at: datetime
    onset_at: datetime | None = None
    verification_status: VerificationStatus
    encounter_id: str


class Procedure(Frozen):
    """Domain 5 — supports billed procedures and reveals timing conflicts."""

    procedure_id: str
    code_system: str
    code: str
    status: EventStatus
    performed_at: datetime
    performer_id: str | None = None
    location_id: str | None = None
    encounter_id: str


class MedicationKind(StrEnum):
    REQUEST = "request"
    DISPENSE = "dispense"


class MedicationEvent(Frozen):
    """Domain 6 — supports billed medication lines."""

    medication_id: str
    kind: MedicationKind
    code_system: str
    code: str
    status: EventStatus
    quantity: Decimal
    occurred_at: datetime
    encounter_id: str


class DiagnosticKind(StrEnum):
    SERVICE_REQUEST = "service_request"
    OBSERVATION = "observation"
    DIAGNOSTIC_REPORT = "diagnostic_report"


class DiagnosticEvent(Frozen):
    """Domain 7 — supports test-related evidence.

    The prototype checks that a test happened; it never interprets clinical values.
    """

    diagnostic_id: str
    kind: DiagnosticKind
    code_system: str
    code: str
    status: EventStatus
    effective_at: datetime
    result_at: datetime | None = None
    encounter_id: str


class DocumentRef(Frozen):
    """Domain 8 — clone/similarity detection and provenance.

    `text_hash` exists so similarity can run without moving narrative text around more than
    necessary; `text` is optional and omitted from list responses.
    """

    document_id: str
    kind: str
    text: str | None = None
    text_hash: str
    author_id: str | None = None
    authored_at: datetime
    encounter_id: str


# --------------------------------------------------------------------------------------
# Domain 9 — billing resources
# --------------------------------------------------------------------------------------


class Account(Frozen):
    account_id: str
    participant_id: str
    provider_id: str
    status: str


class ChargeItem(Frozen):
    charge_item_id: str
    account_id: str
    code_system: str
    code: str
    quantity: Decimal
    unit_price: Decimal
    total_amount: Decimal
    occurred_at: datetime
    encounter_id: str


class Invoice(Frozen):
    invoice_id: str
    account_id: str
    total_amount: Decimal
    issued_at: datetime
    charge_item_refs: tuple[ResourceRef, ...] = ()


# --------------------------------------------------------------------------------------
# Bundle
# --------------------------------------------------------------------------------------


class CanonicalBundle(Frozen):
    """One claim and everything that should support it.

    **Note what is absent:** there is no scenario or label field anywhere on this type. The
    demo scenario label lives on `DemoMetadata`, which is a sibling — never a member. That
    separation is structural, so a detector cannot reach the answer key even by accident.
    See `docs/canonical/04_data_card.md` § Leakage controls.
    """

    bundle_id: str
    claim: ClaimHeader
    lines: tuple[ClaimLine, ...]
    encounters: tuple[Encounter, ...] = ()
    conditions: tuple[Condition, ...] = ()
    procedures: tuple[Procedure, ...] = ()
    medications: tuple[MedicationEvent, ...] = ()
    diagnostics: tuple[DiagnosticEvent, ...] = ()
    documents: tuple[DocumentRef, ...] = ()
    accounts: tuple[Account, ...] = ()
    charge_items: tuple[ChargeItem, ...] = ()
    invoices: tuple[Invoice, ...] = ()
    provenance: tuple[Provenance, ...] = ()

    def resource_index(self) -> dict[tuple[str, str], object]:
        """Every resource keyed by (type, id), for reference resolution."""
        index: dict[tuple[str, str], object] = {
            (ResourceType.CLAIM, self.claim.claim_id): self.claim
        }
        groups: tuple[tuple[ResourceType, tuple, str], ...] = (
            (ResourceType.CLAIM_LINE, self.lines, "line_id"),
            (ResourceType.ENCOUNTER, self.encounters, "encounter_id"),
            (ResourceType.CONDITION, self.conditions, "condition_id"),
            (ResourceType.PROCEDURE, self.procedures, "procedure_id"),
            (ResourceType.MEDICATION, self.medications, "medication_id"),
            (ResourceType.DIAGNOSTIC, self.diagnostics, "diagnostic_id"),
            (ResourceType.DOCUMENT, self.documents, "document_id"),
            (ResourceType.ACCOUNT, self.accounts, "account_id"),
            (ResourceType.CHARGE_ITEM, self.charge_items, "charge_item_id"),
            (ResourceType.INVOICE, self.invoices, "invoice_id"),
        )
        for resource_type, items, id_field in groups:
            for item in items:
                index[(resource_type, getattr(item, id_field))] = item
        return index

    def unresolved_refs(self) -> tuple[ResourceRef, ...]:
        """Every reference in the bundle that does not resolve to a present resource."""
        index = self.resource_index()
        missing: list[ResourceRef] = []
        for line in self.lines:
            candidates = list(line.supporting_refs)
            if line.charge_item_ref is not None:
                candidates.append(line.charge_item_ref)
            missing.extend(ref for ref in candidates if ref.key() not in index)
        for invoice in self.invoices:
            missing.extend(ref for ref in invoice.charge_item_refs if ref.key() not in index)
        return tuple(missing)


class DemoMetadata(Frozen):
    """Scenario label for the five seeded demo cases — **display only**.

    Deliberately a sibling of `CanonicalBundle`, never a field on it. It exists so the ingest
    screen can name the case a presenter picked. It must never enter detector features, and
    `tests/test_leakage_separation.py` asserts that it cannot.
    """

    bundle_id: str
    scenario_label: str
    description: str

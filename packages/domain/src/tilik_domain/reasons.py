"""Reason catalog — every reason the engine may emit, and the evidence it must carry.

This is the contract between the rule engine, the UI, and the tests. The UI never composes
its own sentence: queue and case detail read the same `sentence_id` from here, so they can
never disagree about why a case was raised.

Two rules govern the wording, both from `docs/canonical/07_privacy_threat_model.md`:

* The system reports **risk or anomaly requiring review**. It never states fraud.
* Absence of evidence in an incomplete record is **not** evidence a service was not
  delivered. Reasons say what was searched and what was missing, not what someone did.
"""
from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from tilik_domain.canonical import ResourceType
from tilik_domain.versioning import RULESET_VERSION


class RiskMode(StrEnum):
    """The four officially listed facility risk modes this prototype addresses."""

    PHANTOM_OR_NO_PROCEDURE_EVIDENCE = "PHANTOM_OR_NO_PROCEDURE_EVIDENCE"
    REPEAT_BILLING = "REPEAT_BILLING"
    CLONED_DOCUMENTATION = "CLONED_DOCUMENTATION"
    UNBUNDLING_FRAGMENTATION = "UNBUNDLING_FRAGMENTATION"


class PriorityBand(StrEnum):
    """Queue ordering bands.

    `NO_OBSERVED_RISK` means no selected detector fired at this engine version. It must never
    be rendered as "clean" or "safe" — the system is not entitled to that claim.
    """

    DETERMINISTIC_CONFLICT = "DETERMINISTIC_CONFLICT"
    HIGH_PRIORITY_SIGNAL = "HIGH_PRIORITY_SIGNAL"
    NEEDS_CONTEXT = "NEEDS_CONTEXT"
    NO_OBSERVED_RISK = "NO_OBSERVED_RISK"


class CaseState(StrEnum):
    """Functional state model from the master plan § 10."""

    NEW = "NEW"
    SCREENED = "SCREENED"
    IN_REVIEW = "IN_REVIEW"
    EVIDENCE_REQUESTED = "EVIDENCE_REQUESTED"
    DISMISSED = "DISMISSED"
    CONFIRMED_ANOMALY = "CONFIRMED_ANOMALY"
    ESCALATED = "ESCALATED"
    INVALID_INPUT = "INVALID_INPUT"


ALLOWED_TRANSITIONS: dict[CaseState, frozenset[CaseState]] = {
    CaseState.NEW: frozenset({CaseState.SCREENED, CaseState.INVALID_INPUT}),
    CaseState.SCREENED: frozenset({CaseState.IN_REVIEW}),
    CaseState.IN_REVIEW: frozenset(
        {
            CaseState.EVIDENCE_REQUESTED,
            CaseState.DISMISSED,
            CaseState.CONFIRMED_ANOMALY,
            CaseState.ESCALATED,
        }
    ),
    # A new bundle version re-screens the case.
    CaseState.EVIDENCE_REQUESTED: frozenset({CaseState.SCREENED}),
    # Reopenable by an authorized reviewer.
    CaseState.DISMISSED: frozenset({CaseState.IN_REVIEW}),
    CaseState.CONFIRMED_ANOMALY: frozenset({CaseState.ESCALATED}),
    # No automated sanction or payment action follows escalation.
    CaseState.ESCALATED: frozenset(),
    CaseState.INVALID_INPUT: frozenset({CaseState.NEW}),
}


class DispositionAction(StrEnum):
    """The four actions a human reviewer may take.

    None of them is a verdict. `CONFIRM_ANOMALY` means the reviewer agrees an inconsistency
    exists — it is not a finding of fraud, and the UI must say so before accepting it.
    """

    REJECT_SIGNAL = "REJECT_SIGNAL"
    REQUEST_EVIDENCE = "REQUEST_EVIDENCE"
    CONFIRM_ANOMALY = "CONFIRM_ANOMALY"
    ESCALATE = "ESCALATE"


class ReasonCode(StrEnum):
    """Stable identifiers used by the UI and by tests. Never renumbered."""

    LINE_WITHOUT_COMPLETED_PROCEDURE = "LINE_WITHOUT_COMPLETED_PROCEDURE"
    LINE_WITHOUT_MEDICATION_DISPENSE = "LINE_WITHOUT_MEDICATION_DISPENSE"
    SUPPORTING_EVIDENCE_ENTERED_IN_ERROR = "SUPPORTING_EVIDENCE_ENTERED_IN_ERROR"
    OVERLAPPING_CLAIM_SAME_EPISODE = "OVERLAPPING_CLAIM_SAME_EPISODE"
    DUPLICATE_CLAIM_FINGERPRINT = "DUPLICATE_CLAIM_FINGERPRINT"
    NEAR_DUPLICATE_DOCUMENTATION = "NEAR_DUPLICATE_DOCUMENTATION"
    EPISODE_SPLIT_ACROSS_CLAIMS = "EPISODE_SPLIT_ACROSS_CLAIMS"


class ReasonDefinition(BaseModel):
    """One catalog entry."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    code: ReasonCode
    mode: RiskMode
    sentence_id: str
    """Working-language sentence the reviewer reads. No model jargon, no accusation."""
    required_evidence: tuple[ResourceType, ...]
    """Resource types that must accompany this reason for it to be valid.

    This is about the **reason**: what the engine has to be able to point at before the reason
    is well formed. It is not what the reviewer is looking for — see `expected_support`.
    """
    expected_support: tuple[ResourceType, ...] = ()
    """Resource types that should stand behind the billed line, had the service been recorded.

    This is about the **claim**, and the two diverge exactly where it matters most. A reason
    saying "this line has no completed procedure record" *requires* the line and the visit to be
    citable, and *expects* a `Procedure` that is not there. Rendering `required_evidence` as
    "bukti yang diharapkan" told a reviewer everything expected had been found, on a case whose
    whole finding is that something is missing.

    Defaults to `required_evidence` when a reason draws no distinction between the two.
    """
    deterministic: bool
    """True when a versioned invariant is violated outright, rather than inferred."""
    ruleset_version: str = RULESET_VERSION


def _build_catalog() -> dict[ReasonCode, ReasonDefinition]:
    definitions = (
        ReasonDefinition(
            code=ReasonCode.LINE_WITHOUT_COMPLETED_PROCEDURE,
            mode=RiskMode.PHANTOM_OR_NO_PROCEDURE_EVIDENCE,
            sentence_id="Baris tindakan ini tidak punya catatan tindakan yang selesai.",
            required_evidence=(ResourceType.CLAIM_LINE, ResourceType.ENCOUNTER),
            expected_support=(ResourceType.PROCEDURE, ResourceType.ENCOUNTER),
            deterministic=True,
        ),
        ReasonDefinition(
            code=ReasonCode.LINE_WITHOUT_MEDICATION_DISPENSE,
            mode=RiskMode.PHANTOM_OR_NO_PROCEDURE_EVIDENCE,
            sentence_id="Baris obat ini tidak punya catatan penyerahan obat.",
            required_evidence=(ResourceType.CLAIM_LINE, ResourceType.ENCOUNTER),
            expected_support=(ResourceType.MEDICATION, ResourceType.ENCOUNTER),
            deterministic=True,
        ),
        ReasonDefinition(
            code=ReasonCode.SUPPORTING_EVIDENCE_ENTERED_IN_ERROR,
            mode=RiskMode.PHANTOM_OR_NO_PROCEDURE_EVIDENCE,
            sentence_id="Bukti pendukung baris ini ditandai keliru-input.",
            required_evidence=(ResourceType.CLAIM_LINE, ResourceType.PROCEDURE),
            deterministic=True,
        ),
        ReasonDefinition(
            code=ReasonCode.OVERLAPPING_CLAIM_SAME_EPISODE,
            mode=RiskMode.REPEAT_BILLING,
            sentence_id="Klaim lain pada episode yang sama memuat baris yang bertumpang tindih.",
            required_evidence=(ResourceType.CLAIM, ResourceType.CLAIM_LINE),
            deterministic=True,
        ),
        ReasonDefinition(
            code=ReasonCode.DUPLICATE_CLAIM_FINGERPRINT,
            mode=RiskMode.REPEAT_BILLING,
            sentence_id="Sidik klaim ini identik dengan klaim lain.",
            required_evidence=(ResourceType.CLAIM,),
            deterministic=True,
        ),
        ReasonDefinition(
            code=ReasonCode.NEAR_DUPLICATE_DOCUMENTATION,
            mode=RiskMode.CLONED_DOCUMENTATION,
            sentence_id="Dokumentasi kunjungan ini sangat mirip dengan kunjungan lain.",
            required_evidence=(ResourceType.DOCUMENT, ResourceType.ENCOUNTER),
            deterministic=False,
        ),
        ReasonDefinition(
            code=ReasonCode.EPISODE_SPLIT_ACROSS_CLAIMS,
            mode=RiskMode.UNBUNDLING_FRAGMENTATION,
            sentence_id="Layanan satu episode tampak terpecah ke beberapa klaim berdekatan.",
            required_evidence=(ResourceType.CLAIM, ResourceType.ENCOUNTER),
            deterministic=True,
        ),
    )
    return {
        definition.code: (
            definition
            if definition.expected_support
            # A reason that draws no distinction expects exactly what it requires; filling it
            # here rather than at every call site keeps the field non-optional for readers.
            else definition.model_copy(update={"expected_support": definition.required_evidence})
        )
        for definition in definitions
    }


REASON_CATALOG: dict[ReasonCode, ReasonDefinition] = _build_catalog()


def definition_for(code: ReasonCode) -> ReasonDefinition:
    """Look up a reason definition. Raises when a code is not catalogued."""
    try:
        return REASON_CATALOG[code]
    except KeyError as exc:  # pragma: no cover - guarded by test_reason_catalog
        raise KeyError(f"Reason code {code!r} is not in the catalog") from exc


def codes_for_mode(mode: RiskMode) -> tuple[ReasonCode, ...]:
    """Every reason code belonging to one risk mode."""
    return tuple(
        definition.code for definition in REASON_CATALOG.values() if definition.mode is mode
    )

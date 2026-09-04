"""Record a human decision: state machine, optimistic locking, audit event.

Three guarantees, each defending against a different way accountability fails.

**A reason is always required.** Not because a form asks for one, but because a decision no one
can explain is not reviewable. Enforced in the DTO, again at event construction, and again by a
database check constraint — the UI can be bypassed and internal callers can be careless.

**A stale write is refused and nothing is recorded.** If a reviewer acts on version 3 while a
colleague already moved the case to version 4, silently applying their decision would overwrite a
judgement they never saw. The rejection names what changed so they can look before deciding again.

**Nothing here rejects a claim, stops a payment, imposes a sanction, or changes a code.** Those
are not omissions to be filled in later; `docs/canonical/01_product_decision.md` puts them out of
scope, and `test_no_action_triggers_payment_or_sanction` asserts the code has no such path.
`CONFIRM_ANOMALY` means a reviewer agrees an inconsistency exists — nothing more.
"""
from __future__ import annotations

from dataclasses import dataclass

from tilik_domain.canonical import ResourceRef, ResourceType
from tilik_domain.reasons import ALLOWED_TRANSITIONS, CaseState, DispositionAction
from tilik_domain.versioning import EngineIdentity

from app.errors import ErrorCode
from app.service.access import CAPABILITIES, Capability, has_capability
from app.store.audit import AuditEventRecord, AuditStore, new_event_id, occurred_now
from app.store.cases import CaseRecord, CaseStore

ACTION_TO_STATE: dict[DispositionAction, CaseState] = {
    DispositionAction.REJECT_SIGNAL: CaseState.DISMISSED,
    DispositionAction.REQUEST_EVIDENCE: CaseState.EVIDENCE_REQUESTED,
    DispositionAction.CONFIRM_ANOMALY: CaseState.CONFIRMED_ANOMALY,
    DispositionAction.ESCALATE: CaseState.ESCALATED,
}
"""Which state each action moves a case to. No action maps to anything outside the state model."""

AUDIT_READER_ROLES: frozenset[str] = frozenset(
    str(role) for role, caps in CAPABILITIES.items() if Capability.READ_CASE_AUDIT in caps
)
"""Roles permitted to read a case's history.

The audit trail names people and their decisions, so reading it is itself an access decision.
Derived from the ADR-0006 § 2 matrix rather than restated, so the two cannot drift apart —
`auditor` was retired there, and this set follows without needing to be edited again.
"""

REOPEN_ROLES: frozenset[str] = frozenset(
    str(role) for role, caps in CAPABILITIES.items() if Capability.REOPEN_DISMISSED_CASE in caps
)
"""Who may reopen a dismissed case. Reopening appends; it never erases the dismissal."""


@dataclass(frozen=True)
class DispositionRefused(Exception):
    """The decision was not recorded, and no partial event was written."""

    code: ErrorCode
    detail: str

    def __str__(self) -> str:
        return self.detail


@dataclass(frozen=True)
class DispositionOutcome:
    case: CaseRecord
    event: AuditEventRecord


def apply_disposition(
    case: CaseRecord,
    *,
    action: DispositionAction,
    structured_reason: str,
    expected_case_version: int,
    actor_role: str,
    note: str | None = None,
    requested_evidence: tuple[ResourceType, ...] = (),
    supersedes_event_id: str | None = None,
    identity: EngineIdentity | None = None,
    case_store: CaseStore,
    audit_store: AuditStore,
) -> DispositionOutcome:
    """Validate, transition, and record — or refuse and write nothing."""
    if not structured_reason.strip():
        raise DispositionRefused(
            ErrorCode.DISPOSITION_REASON_REQUIRED,
            "A disposition requires a reason. Whitespace is not a reason.",
        )

    if expected_case_version != case.case_version:
        raise DispositionRefused(
            ErrorCode.CASE_VERSION_CONFLICT,
            (
                f"This case moved to version {case.case_version} while you were reviewing "
                f"version {expected_case_version}; its state is now {case.state}. "
                "Reload and decide again — your decision was not recorded."
            ),
        )

    target = ACTION_TO_STATE[action]
    allowed = ALLOWED_TRANSITIONS.get(case.state, frozenset())
    if target not in allowed:
        if case.state is CaseState.DISMISSED and target is not CaseState.IN_REVIEW:
            raise DispositionRefused(
                ErrorCode.DISPOSITION_INVALID_TRANSITION,
                f"A dismissed case must be reopened before it can move to {target}.",
            )
        raise DispositionRefused(
            ErrorCode.DISPOSITION_INVALID_TRANSITION,
            f"{case.state} cannot move to {target}. Allowed from here: "
            f"{', '.join(sorted(str(state) for state in allowed)) or 'nothing'}.",
        )

    evidence = tuple(
        ResourceRef(resource_type=resource_type, resource_id="requested")
        for resource_type in requested_evidence
    )

    event = AuditEventRecord(
        event_id=new_event_id(),
        case_id=case.case_id,
        event_kind="SUPERSEDE" if supersedes_event_id else "DISPOSITION",
        actor_role=actor_role,
        action=action,
        structured_reason=structured_reason.strip(),
        note=note,
        evidence=evidence,
        state_before=case.state,
        state_after=target,
        case_version_before=case.case_version,
        case_version_after=case.case_version + 1,
        supersedes_event_id=supersedes_event_id,
        identity=identity or EngineIdentity(),
        occurred_at=occurred_now(),
    )

    # The event is written first. A case that moved without a recorded reason would be worse
    # than a decision that failed to apply: the first is unexplainable, the second is retryable.
    audit_store.append(event)
    updated = case.model_copy(
        update={
            "state": target,
            "case_version": case.case_version + 1,
            "completeness_notes": case.completeness_notes,
        }
    )
    case_store.save(updated)
    return DispositionOutcome(case=updated, event=event)


def open_for_review(
    case: CaseRecord, *, actor_role: str, case_store: CaseStore, audit_store: AuditStore
) -> CaseRecord:
    """Move a screened case into review, so a disposition has a valid state to leave from.

    Reopening a *dismissed* case is the same transition and is restricted: it revisits someone
    else's recorded judgement. The dismissal is never erased — the reopen is appended beside it.
    """
    if case.state is CaseState.DISMISSED and not has_capability(
        actor_role, Capability.REOPEN_DISMISSED_CASE
    ):
        raise DispositionRefused(
            ErrorCode.CASE_REOPEN_FORBIDDEN,
            f"Role {actor_role!r} may not reopen a dismissed case.",
        )
    if CaseState.IN_REVIEW not in ALLOWED_TRANSITIONS.get(case.state, frozenset()):
        raise DispositionRefused(
            ErrorCode.DISPOSITION_INVALID_TRANSITION,
            f"{case.state} cannot move to {CaseState.IN_REVIEW}.",
        )

    event = AuditEventRecord(
        event_id=new_event_id(),
        case_id=case.case_id,
        event_kind="OPENED",
        actor_role=actor_role,
        state_before=case.state,
        state_after=CaseState.IN_REVIEW,
        case_version_before=case.case_version,
        case_version_after=case.case_version + 1,
        identity=EngineIdentity(),
        occurred_at=occurred_now(),
    )
    audit_store.append(event)
    updated = case.model_copy(
        update={"state": CaseState.IN_REVIEW, "case_version": case.case_version + 1}
    )
    case_store.save(updated)
    return updated


def may_read_audit(actor_role: str) -> bool:
    return has_capability(actor_role, Capability.READ_CASE_AUDIT)

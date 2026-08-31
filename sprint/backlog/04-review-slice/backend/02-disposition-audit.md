# Task 02 — Disposition with optimistic locking and append-only audit

**Stack:** backend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** ✅ Done
**Foundation:** no
**Autonomous:** yes
**Depends on:**
- [`./01-case-endpoints.md`](./01-case-endpoints.md)

## Goal

Record a human decision as an immutable audit event, and make it impossible to overwrite
someone else's decision unknowingly.

## Files to touch

- `apps/backend/app/router/dispositions.py` — `POST /v1/cases/{id}/dispositions`, `GET /v1/cases/{id}/audit`
- `apps/backend/app/service/disposition.py` — state machine plus optimistic locking
- `apps/backend/app/store/audit.py` — append-only event store
- `apps/backend/migrations/` — audit table with an append-only constraint
- `apps/backend/tests/test_disposition.py`

## Skills to consult

- `brief/04_DETAIL_KASUS_DISPOSISI.md` § 4.3 — the concurrent-edit flow
- `docs/canonical/07_privacy_threat_model.md` § Human accountability

## TODOs

- [x] Four actions: reject signal · request evidence · confirm anomaly · escalate
- [x] **Reason is required at the storage layer**, not only in the UI — the UI can be bypassed
- [x] Optimistic locking on the expected case version
- [x] Version mismatch returns a specific error naming what changed
- [x] Audit event records actor, action, reason, note, evidence refs, rule and model version, before/after case version, timestamp
- [x] **Append-only enforced by a database constraint**, not by convention
- [x] Corrections append a superseding event; the original stays visible and linked
- [x] State machine follows the functional state model — no undefined transitions
- [x] Audit read restricted to an authorized role
- [x] Request-evidence moves the case to evidence-requested and records the requested resources
- [x] **No action may trigger claim rejection, payment action, sanction, or code change** — assert this in tests
- [x] Audit events are written whole or not at all — never partially
- [x] **Test:** a disposition without a reason is rejected at the storage layer
- [x] **Test:** a stale-version write is rejected, and no event is written
- [x] **Test:** an UPDATE or DELETE against the audit table fails
- [x] **Test:** a correction produces two visible events with an explicit supersede link
- [x] **Edge case — concurrent dispositions:** second writer rejected, first preserved
- [x] **Edge case — reopening a dismissed case:** allowed for an authorized role, appended not overwritten

## Done when

A disposition without a reason is rejected at the storage layer; a stale-version write is
rejected with nothing written; an UPDATE against the audit table fails; and a correction
leaves both events visible with an explicit supersede link.

> Overwriting someone else's recorded decision is an **accountability failure**, not a
> concurrency inconvenience. The locking and the append-only constraint are the product, not
> polish on top of it.

## Closing checklist

- [x] All `## TODOs` items above are `[x]`
- [x] Done-when assertion verified
- [x] Top-of-file header literally reads `**Status:** ✅ Done`
- [x] Changelog entry appended to `changelog/backend.md`

## Notes

**A reason is required at three layers, and that is not excessive.** The DTO validates it, the
audit record refuses to construct without it, and a Postgres check constraint rejects the row.
The UI can be bypassed; an internal caller can skip the DTO; only the database catches
everything. This is the one field that makes a decision accountable.

**Append-only is a database trigger, not a convention.** `audit_events` has `BEFORE UPDATE` and
`BEFORE DELETE` triggers that raise. Verified live: both statements are refused with
*"audit_events is append-only"* and the row survives. A convention would let anything holding a
connection rewrite history, and a history that can be edited is not a history.

**The audit event is written before the case moves.** A case that changed state with no recorded
reason is unexplainable; a decision that failed to apply is merely retryable. The worse failure
is the one that is prevented.

**`X-Actor-Role` is role simulation, not authentication.** Named plainly rather than dressed up
as a token, so nobody mistakes it for a security control — enterprise IAM is out of scope, and a
header that looked like a Bearer credential would invite exactly that confusion.

`test_no_action_triggers_payment_rejection_or_sanction` walks the service's **syntax tree** rather
than scanning its text: the module docstring names payment and sanction precisely to rule them
out, so a text search would flag the prohibition itself.

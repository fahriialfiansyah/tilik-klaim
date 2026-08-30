# Task 02 — Disposition with optimistic locking and append-only audit

**Stack:** backend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** 📋 Planned
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

- [ ] Four actions: reject signal · request evidence · confirm anomaly · escalate
- [ ] **Reason is required at the storage layer**, not only in the UI — the UI can be bypassed
- [ ] Optimistic locking on the expected case version
- [ ] Version mismatch returns a specific error naming what changed
- [ ] Audit event records actor, action, reason, note, evidence refs, rule and model version, before/after case version, timestamp
- [ ] **Append-only enforced by a database constraint**, not by convention
- [ ] Corrections append a superseding event; the original stays visible and linked
- [ ] State machine follows the functional state model — no undefined transitions
- [ ] Audit read restricted to an authorized role
- [ ] Request-evidence moves the case to evidence-requested and records the requested resources
- [ ] **No action may trigger claim rejection, payment action, sanction, or code change** — assert this in tests
- [ ] Audit events are written whole or not at all — never partially
- [ ] **Test:** a disposition without a reason is rejected at the storage layer
- [ ] **Test:** a stale-version write is rejected, and no event is written
- [ ] **Test:** an UPDATE or DELETE against the audit table fails
- [ ] **Test:** a correction produces two visible events with an explicit supersede link
- [ ] **Edge case — concurrent dispositions:** second writer rejected, first preserved
- [ ] **Edge case — reopening a dismissed case:** allowed for an authorized role, appended not overwritten

## Done when

A disposition without a reason is rejected at the storage layer; a stale-version write is
rejected with nothing written; an UPDATE against the audit table fails; and a correction
leaves both events visible with an explicit supersede link.

> Overwriting someone else's recorded decision is an **accountability failure**, not a
> concurrency inconvenience. The locking and the append-only constraint are the product, not
> polish on top of it.

## Closing checklist

- [ ] All `## TODOs` items above are `[x]`
- [ ] Done-when assertion verified
- [ ] Top-of-file header literally reads `**Status:** ✅ Done`
- [ ] Changelog entry appended to `changelog/backend.md`

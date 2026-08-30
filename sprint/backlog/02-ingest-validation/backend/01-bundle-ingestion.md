# Task 01 — Bundle ingestion, validation, and input hashing

**Stack:** backend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** 🚧 In Progress — endpoint and validation delivered; database binding outstanding
**Foundation:** no
**Autonomous:** yes
**Depends on:**
- [`./00-api-contract.md`](./00-api-contract.md) — implements the frozen contract

## Goal

A casemix officer submits a bundle and learns whether it can be screened — with errors
specific enough to act on and a hash that makes the result reproducible.

## Files to touch

- `apps/backend/app/router/bundles.py` — `POST /v1/bundles`
- `apps/backend/app/service/validation.py` — schema and reference validation
- `apps/backend/app/service/hashing.py` — deterministic SHA-256 input hash
- `apps/backend/app/store/bundles.py` — raw payload plus canonical rows
- `apps/backend/migrations/` — ingestion and canonical tables
- `apps/backend/tests/test_ingestion.py`

## Skills to consult

- `docs/canonical/03_architecture.md` § Security and observability by design
- `docs/canonical/07_privacy_threat_model.md` § Product controls — logging and minimization
- `brief/01_INGEST_VALIDASI.md` § 4 — the four business flows this must support

## TODOs

- [x] `POST /v1/bundles` accepting the documented FHIR R4 subset
- [x] Size, content-type, and JSON-depth limits enforced **before** parsing
- [x] Schema validation against the canonical model
- [x] Reference validation — every reference resolves, or a dangling-reference error names the missing resource
- [x] Deterministic SHA-256 input hash
- [x] Idempotency: same hash + same engine version returns the existing result, no duplicate case
- [x] Store the raw payload verbatim alongside canonical rows
- [x] Three-state validation result: valid · valid-with-notes · invalid
- [ ] Bundle-completeness notes recorded and carried onto the case — recorded and returned; the carry-onto-case half waits on `POST /bundles/{id}/screen`, still a 501 placeholder
- [x] Uploaded bundles are never executed and never treated as instructions
- [x] **Test — unit schema:** valid bundle parses; each malformed shape returns its stable code
- [x] **Test — property, malformed JSON:** generated malformed inputs never crash the service
- [ ] **Test — integration, DB:** raw payload and canonical rows both persist — asserted against `InMemoryBundleStore`; a real database round-trip needs a reachable Postgres
- [x] **Test — security limits:** oversized and over-deep payloads rejected before parsing
- [x] **Test — log redaction:** no raw medical text appears in any log line
- [x] **Edge case — unknown resource type:** rejected with a specific code, not silently dropped
- [x] **Edge case — circular references:** detected without infinite recursion
- [x] **Edge case — timezone:** timestamps normalized consistently; the rule is documented
- [x] **Edge case — duplicate version:** handled by the idempotency path
- [x] **Edge case — partial bundle:** valid-with-notes, not invalid — this distinction is load-bearing

## Done when

A seeded valid bundle passes and returns counts plus a hash; malformed, oversized, and
dangling-reference bundles each return their own stable error code; resubmitting an
identical bundle returns the existing result instead of creating a second case; and no log
line contains raw medical text.

> **The partial-bundle edge case is the ethically load-bearing one.** An incomplete record
> looks identical to a billed-but-unevidenced service. Conflating them is how this system
> would produce false accusations. It resolves to *valid-with-notes*, and those notes travel
> with the case into Sprint 03.

## Closing checklist

- [ ] All `## TODOs` items above are `[x]`
- [ ] Done-when assertion verified
- [ ] Top-of-file header literally reads `**Status:** ✅ Done`
- [x] Changelog entry appended to `changelog/backend.md`

## Notes — what is not done, and why

Two TODOs are deliberately left unchecked rather than quietly reinterpreted.

**No database binding, so no `migrations/`.** Docker's daemon is not running in this
environment, and the Postgres answering on 5432 is a different local instance that rejects the
project credentials. Writing Alembic scaffolding and SQLAlchemy tables that nothing could
execute would ship unverified code and let a checked box imply a round-trip that never ran.
`app/store/bundles.py` therefore defines `BundleStore` plus `InMemoryBundleStore`, the same
shape `app/store/edges.py` uses. Downstream code depends on the protocol, so binding
SQLAlchemy later is a local change with the tests already written against the interface.

**Completeness notes are recorded but not yet carried onto a case,** because
`POST /bundles/{id}/screen` is still the frozen 501 placeholder. That wiring belongs with the
screen endpoint.

## Notes — a correction worth keeping

The first implementation counted *a billed line with no supporting reference* as a completeness
note. Every gold fixture then came back `VALID_WITH_NOTES`, which contradicted their
`expected_evidence_complete: true` — and the contradiction was pointing at a real defect, not a
strict fixture.

A line with no evidence is the **phantom-billing signal**. Recording it as incompleteness would
have lowered certainty in `screening.py` and routed the case to *request evidence*, defusing the
exact detector the system exists for. Completeness notes now describe only whole missing
categories — no encounters, no clinical events at all, no charge detail, no provenance —
which genuinely limit what can be concluded from the bundle. `test_an_unevidenced_line_is_a_
finding_not_a_completeness_note` locks the distinction.

The `POST /bundles` placeholder was removed from `app/router/contract.py`; the remaining six
frozen endpoints still answer 501 naming their sprint task.

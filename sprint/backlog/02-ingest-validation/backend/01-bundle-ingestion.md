# Task 01 — Bundle ingestion, validation, and input hashing

**Stack:** backend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** 📋 Planned
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

- [ ] `POST /v1/bundles` accepting the documented FHIR R4 subset
- [ ] Size, content-type, and JSON-depth limits enforced **before** parsing
- [ ] Schema validation against the canonical model
- [ ] Reference validation — every reference resolves, or a dangling-reference error names the missing resource
- [ ] Deterministic SHA-256 input hash
- [ ] Idempotency: same hash + same engine version returns the existing result, no duplicate case
- [ ] Store the raw payload verbatim alongside canonical rows
- [ ] Three-state validation result: valid · valid-with-notes · invalid
- [ ] Bundle-completeness notes recorded and carried onto the case
- [ ] Uploaded bundles are never executed and never treated as instructions
- [ ] **Test — unit schema:** valid bundle parses; each malformed shape returns its stable code
- [ ] **Test — property, malformed JSON:** generated malformed inputs never crash the service
- [ ] **Test — integration, DB:** raw payload and canonical rows both persist
- [ ] **Test — security limits:** oversized and over-deep payloads rejected before parsing
- [ ] **Test — log redaction:** no raw medical text appears in any log line
- [ ] **Edge case — unknown resource type:** rejected with a specific code, not silently dropped
- [ ] **Edge case — circular references:** detected without infinite recursion
- [ ] **Edge case — timezone:** timestamps normalized consistently; the rule is documented
- [ ] **Edge case — duplicate version:** handled by the idempotency path
- [ ] **Edge case — partial bundle:** valid-with-notes, not invalid — this distinction is load-bearing

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
- [ ] Changelog entry appended to `changelog/backend.md`

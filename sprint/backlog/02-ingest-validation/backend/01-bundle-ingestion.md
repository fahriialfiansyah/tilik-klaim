# Task 01 — Bundle ingestion, validation, and input hashing

**Stack:** backend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** ✅ Done
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
- [x] Bundle-completeness notes recorded and carried onto the case — `POST /bundles/{id}/screen` was implemented here so the notes actually reach a reviewer
- [x] Uploaded bundles are never executed and never treated as instructions
- [x] **Test — unit schema:** valid bundle parses; each malformed shape returns its stable code
- [x] **Test — property, malformed JSON:** generated malformed inputs never crash the service
- [x] **Test — integration, DB:** raw payload and canonical rows both persist — `tests/test_store_postgres.py`, 12 tests against a live Postgres
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

- [x] All `## TODOs` items above are `[x]`
- [x] Done-when assertion verified
- [x] Top-of-file header literally reads `**Status:** ✅ Done`
- [x] Changelog entry appended to `changelog/backend.md`

## Notes — the database layer

Postgres is bound and the migration is applied. `migrations/` runs Alembic with the URL taken
from `app.config`, never from `alembic.ini`: a connection string duplicated in two files is the
one that leaks from whichever copy nobody updates, and it would let a migration run against a
different database than the service uses.

`raw_payload` is `TEXT`, not `JSONB`, and that is the load-bearing choice in `store/tables.py`.
JSONB normalises — reordering keys, dropping whitespace, rewriting numbers — which is exactly
what "stored verbatim" must not do. The raw payload exists so a result can be re-derived from
precisely what arrived. The canonical form lives beside it in `bundle_json`, where normalising
is welcome. A test asserts the byte-for-byte round trip.

Both stores satisfy their protocol, and `store/registry.py` picks between them once per process.
The in-memory fallback is not a convenience: the demo runbook requires an offline run and the
frontend team has no Docker. Verified both ways — 227 pass with Postgres, 215 pass and 12 skip
without it.

Two check constraints back the types up in the database: a status outside the three-state enum
and a confidence outside 0..1 are both refused by Postgres, not only by Pydantic.

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

`POST /bundles` and `POST /bundles/{id}/screen` were both removed from
`app/router/contract.py`; the remaining five frozen endpoints still answer 501 naming their
sprint task.

**The screen endpoint landed here rather than in `04-review-slice`,** because the completeness
notes had nowhere to travel to without it. It creates a minimal case, carries the notes onto it,
and links the case back to its ingestion so a resubmission returns `existing_case_id`. The queue,
disposition flow, audit trail, and the case table itself remain with `04-review-slice`;
`app/store/cases.py` holds only what `ScreenResponse` needs, and says so.

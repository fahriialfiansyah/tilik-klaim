# Task 00 — Freeze the API contract and commit response fixtures

**Stack:** backend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** ✅ Done
**Foundation:** yes
**Autonomous:** yes
**Depends on:**
- [`../../01-synthetic-data/backend/00-canonical-schema.md`](../../01-synthetic-data/backend/00-canonical-schema.md) — response shapes are built from the canonical model

> **Foundation task.** Sprint 04's frontend reads these fixtures. Publishing them early is
> what lets M1 and M2 work in parallel instead of serially — § 20 calls this out explicitly.

## Goal

Publish and freeze the seven-endpoint OpenAPI surface with a committed example response per
endpoint, so the frontend can be built against a stable contract.

## Contract delivered

Seven endpoints from `docs/canonical/03_architecture.md` § Minimal API contracts:

| Endpoint | Key constraint |
|----------|----------------|
| `POST /v1/bundles` | Scenario label must never enter detector features |
| `POST /v1/bundles/{id}/screen` | Idempotent for the same input hash + version |
| `GET /v1/cases` | Pseudonymous fields only |
| `GET /v1/cases/{id}` | No raw sensitive text in the list response |
| `POST /v1/cases/{id}/dispositions` | Optimistic locking; reason required |
| `GET /v1/cases/{id}/audit` | Authorized role only |
| `GET /v1/evaluations/{run_id}` | Synthetic label displayed prominently |

Plus a **stable error-code catalog** — the same failure returns the same code every time.

## Files to touch

- `apps/backend/app/dto/{common,bundles,cases,dispositions,evaluations}.py` — 29 wire models
- `apps/backend/app/router/contract.py` — the seven route declarations
- `apps/backend/app/errors.py` — stable error-code catalog
- `apps/backend/tests/fixtures/api/*.json` — 10 committed example responses
- `apps/backend/tests/fixtures/build_api.py` — deterministic fixture builder
- `docs/api/openapi.json` — exported schema

## Skills to consult

- `docs/canonical/03_architecture.md` § Minimal API contracts and § Security and observability

## TODOs

- [x] Request and response models for all seven endpoints
- [x] Stable error-code catalog with one code per distinct failure mode
- [x] `GET /v1/cases` returns pseudonymous fields only — no raw medical text
- [x] Committed example response per endpoint, usable as a frontend fixture
- [x] Exported OpenAPI schema
- [x] Test: every example fixture validates against its response model
- [x] Announce the freeze in `changelog/backend.md` so M2 knows the contract is safe to build on

## Done when

All seven endpoints appear in the exported OpenAPI schema, each has a committed example
response that validates against its model, and the error-code catalog covers every failure
path in the ingestion task.

## Closing checklist

- [x] All `## TODOs` items above are `[x]`
- [x] Done-when assertion verified
- [x] Top-of-file header literally reads `**Status:** ✅ Done`
- [x] Changelog entry appended to `changelog/backend.md`

## Outcome — 2026-08-30

Contract frozen and published. **Sprint 04's frontend is unblocked** — it can build against
`tests/fixtures/api/*.json` without a running backend.

| Artifact | Result |
|----------|--------|
| Endpoints | 7 published in `docs/api/openapi.json` (plus `/healthz`) |
| Wire models | 29 across five DTO modules, all frozen |
| Error catalog | 18 stable codes, every one mapped to an HTTP status |
| Fixtures | 10 committed, including an invalid-bundle and a version-conflict case |
| Tests | 64 passing in `apps/backend` |

**Routes answer `501` until implemented**, naming the sprint task that fills each one in. The
contract is live and generatable today; a caller that arrives early gets an unambiguous
answer instead of a misleading empty success.

Contract guarantees now locked by tests, not convention:

- `GET /v1/cases` carries **no raw medical text** — asserted against clinical vocabulary.
- Queue rows lead with `reason_sentence`; field order puts it ahead of band and amount.
- Exactly **five** queue metrics, and none may contain "fraud", "saved", or "ranking".
- Reason sentences come from the catalog, so queue and detail cannot disagree.
- A clone reason is band-capped and must carry the template caveat.
- A disposition requires a non-blank reason **and** an `expected_case_version`.

# Task 00 — Freeze the API contract and commit response fixtures

**Stack:** backend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** 📋 Planned
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

- `apps/backend/app/dto/` — request and response models for all seven endpoints
- `apps/backend/app/errors.py` — stable error-code catalog
- `apps/backend/tests/fixtures/api/*.json` — one committed example response per endpoint
- `docs/api/openapi.json` — exported schema

## Skills to consult

- `docs/canonical/03_architecture.md` § Minimal API contracts and § Security and observability

## TODOs

- [ ] Request and response models for all seven endpoints
- [ ] Stable error-code catalog with one code per distinct failure mode
- [ ] `GET /v1/cases` returns pseudonymous fields only — no raw medical text
- [ ] Committed example response per endpoint, usable as a frontend fixture
- [ ] Exported OpenAPI schema
- [ ] Test: every example fixture validates against its response model
- [ ] Announce the freeze in `changelog/backend.md` so M2 knows the contract is safe to build on

## Done when

All seven endpoints appear in the exported OpenAPI schema, each has a committed example
response that validates against its model, and the error-code catalog covers every failure
path in the ingestion task.

## Closing checklist

- [ ] All `## TODOs` items above are `[x]`
- [ ] Done-when assertion verified
- [ ] Top-of-file header literally reads `**Status:** ✅ Done`
- [ ] Changelog entry appended to `changelog/backend.md`

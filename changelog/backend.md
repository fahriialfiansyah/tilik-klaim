# Changelog — Backend

Append-only. Newest entry at the top. Agent and MCP tasks would also land here; this project has none.

---

### 2026-08-30 · [Sprint 02 — ingest-validation](../sprint/backlog/02-ingest-validation/sprint.md) · Task: [API contract](../sprint/backlog/02-ingest-validation/backend/00-api-contract.md) · ✅ Done

**Event:** Task completed — **API CONTRACT FROZEN**
**Files:** `apps/backend/app/dto/`, `apps/backend/app/router/contract.py`, `apps/backend/app/errors.py`, `apps/backend/tests/fixtures/api/`, `docs/api/openapi.json`
> Seven endpoints published with 29 wire models and 18 stable error codes. Ten example
> responses committed. **Sprint 04 frontend may now start in parallel** — build against
> `apps/backend/tests/fixtures/api/*.json`, no running backend needed. Routes answer 501
> naming their implementing task until behaviour lands. Verified: 64 tests passing.

### 2026-08-30 · [Sprint 01 — synthetic-data](../sprint/backlog/01-synthetic-data/sprint.md) · Task: [Canonical schema](../sprint/backlog/01-synthetic-data/backend/00-canonical-schema.md) · ✅ Done

**Event:** Task completed — **FOUNDATION, unblocks Sprints 02/03/04/06**
**Files:** `packages/domain/`, `apps/backend/tests/fixtures/gold/`
> Canonical model over 11 schema domains, 7-entry reason catalog covering all 4 risk modes,
> 10 evidence edge types, and 5 committed gold fixtures. Demo scenario label is structurally
> unreachable from detector features. Verified: 62 tests passing.

### 2026-08-30 · [Sprint 00 — foundation](../sprint/backlog/00-foundation/sprint.md) · Task: [API skeleton](../sprint/backlog/00-foundation/backend/01-api-skeleton.md) · ✅ Done

**Event:** Task completed
**Files:** `apps/backend/`, `docker-compose.yml`, `packages/`, `evaluation/`
> FastAPI service with environment-driven config and `/healthz` reporting engine identity
> plus `data_class: synthetic`. Local Postgres via Docker Compose — no external network.
> Verified: `uv run pytest` → 1 passed on Python 3.11.15.

### 2026-08-30 · Sprints 01–07 · 📋 Added

**Event:** Task created (11 backend tasks)
**Files:** `sprint/backlog/*/backend/*.md`
> WS-001 → sprint 01 (4 tasks, incl. foundation `00-canonical-schema`); WS-002 → sprint 02
> (2 tasks, incl. foundation `00-api-contract`); WS-003 → sprint 03 (2); WS-005 backend →
> sprint 04 (2); WS-004 → sprint 05 (1); WS-006 → sprint 06 (1); § 22 → sprint 07 (1).
> Each task carries its WS Acceptance as `## Done when` and its Tests plus Edge cases as TODOs.

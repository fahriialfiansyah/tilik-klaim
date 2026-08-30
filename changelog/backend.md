# Changelog — Backend

Append-only. Newest entry at the top. Agent and MCP tasks would also land here; this project has none.

---

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

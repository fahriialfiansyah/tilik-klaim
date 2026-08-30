# Task 01 — API skeleton, configuration, and test harness

**Stack:** backend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** ✅ Done
**Foundation:** no
**Autonomous:** no — one-time project setup; not reframeable as a runtime task.

## Goal

A FastAPI service that starts, reports its engine identity on `/healthz`, reads all
configuration from the environment, and has a green test run.

## Files to touch

- `apps/backend/pyproject.toml` — dependencies, pytest and ruff configuration
- `apps/backend/app/config.py` — settings from environment; no hardcoded values
- `apps/backend/app/main.py` — application entrypoint plus the scope guard docstring
- `apps/backend/app/router/health.py` — `/healthz` returning engine and dataset versions
- `apps/backend/app/{service,dto,store}/` — package skeletons for later sprints
- `apps/backend/tests/test_health.py` — first test
- `apps/backend/.env.example` — documented environment contract
- `docker-compose.yml` — local Postgres, no external network

## Skills to consult

- `docs/canonical/03_architecture.md` — component choices, security and observability baseline
- `.claude/rules/architecture.md` — stack enforcement

## TODOs

- [x] `pyproject.toml` with FastAPI, Pydantic, SQLAlchemy, psycopg, Alembic, NetworkX, scikit-learn, pandas
- [x] Settings object reading `DATABASE_URL`, engine/ruleset/dataset versions, ingest limits
- [x] `/healthz` returns status, engine version, ruleset version, dataset version, `data_class: synthetic`
- [x] Scope guard documented at the entrypoint: no fraud verdict, no payment action, no LLM in the risk path
- [x] `docker-compose.yml` with Postgres 16 and a healthcheck
- [x] `.env.example` documenting every variable
- [x] Test asserting `/healthz` shape and the synthetic data class
- [x] `uv run pytest` passes

## Done when

`uv run pytest` in `apps/backend/` reports all tests passing, and `GET /healthz` returns
`200` with `data_class: "synthetic"` plus a non-empty engine version.

**Verified 2026-08-30:** `1 passed` on Python 3.11.15.

## Closing checklist

- [x] All `## TODOs` items above are `[x]`
- [x] Done-when assertion verified (`uv run pytest` → 1 passed)
- [x] Top-of-file header literally reads `**Status:** ✅ Done`
- [x] Changelog entry appended to `changelog/backend.md`

## Notes

Python 3.9.6 is the system interpreter; `uv venv --python 3.11` fetches the required 3.11+
runtime, so no system Python change is needed.

Database choice: plain Postgres via Docker Compose rather than Supabase.
`docs/canonical/03_architecture.md` § Component rationale specifies "PostgreSQL with JSONB",
and this project needs none of Supabase's Auth, Storage, or Realtime layers — roles are
simulated per `brief/00_OVERVIEW.md` § 6.2. Reversible: self-hosted Supabase is Postgres
plus services, so `supabase-init` can be layered on later without a data migration.

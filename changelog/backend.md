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

### 2026-08-30 · [Sprint 03 — evidence-rules](../sprint/backlog/03-evidence-rules/sprint.md) · Task: [Evidence graph](../sprint/backlog/03-evidence-rules/backend/01-evidence-graph.md) · ✅ Done

**Event:** Task completed
**Files:** `apps/backend/app/service/evidence_graph.py`, `apps/backend/app/store/edges.py`, `packages/domain/src/tilik_domain/canonical.py`
> All ten canonical edge types derive over the five gold fixtures, every edge carrying its
> derivation rule and ruleset version; the two inferred cross-claim edges carry a confidence
> and the stated ones do not. Incomplete bundles degrade into recorded `EvidenceGap`s instead
> of raising, so a missing record never reads as a missing service. Output ordering is stable
> under input reordering, so re-screening the same bundle diffs to nothing. Episode grouping
> merges claims sharing an episode unless a follow-up document explains the return visit.
> Edge persistence is keyed by `(bundle_id, ruleset_version)`: re-screening replaces its slice,
> a version bump preserves the old one so prior audit events keep resolving.
> Added `ResourceType.PRACTITIONER` — `AUTHORED_BY` was required by the architecture doc but
> not constructible — plus `ResourceType.is_stored_resource` to separate referenced-only
> identities from dangling refs. Verified: `uv run pytest` → 115 passed (was 64); domain
> → 21 passed; ruff clean on the new files.

### 2026-08-30 · [Sprint 03 — evidence-rules](../sprint/backlog/03-evidence-rules/sprint.md) · Task: [Rule engine](../sprint/backlog/03-evidence-rules/backend/02-rule-engine.md) · ✅ Done

**Event:** Task completed — Sprint 03 closed, Gate G4 met
**Files:** `apps/backend/app/service/rules/`, `apps/backend/app/service/screening.py`
> All five gold fixtures screen to exactly their expected reason codes and nothing more. Four
> risk modes work, not the three the gate required — the clone baseline was delivered rather
> than deferred. Every reason carries resolvable evidence, counter-evidence returned alongside
> rather than as a second lookup, its component scores, and its rule version.
> The three model-card caps are enforced and tested: text similarity alone tops out at
> `NEEDS_CONTEXT`; an incomplete bundle steps the band down and routes to `REQUEST_EVIDENCE`
> instead of toward confirm-anomaly; an exact duplicate is top band and still decides nothing.
> `NO_OBSERVED_RISK` never renders as clean or safe, and a test asserts no reason text contains
> fraud/curang/palsu/tolak/sanksi. Screening the same input hash at the same version is
> byte-identical. Verified: `uv run pytest` → 162 passed (was 115); domain → 21 passed;
> ruff clean on all new files.

### 2026-08-31 · [Sprint 02 — ingest-validation](../sprint/backlog/02-ingest-validation/sprint.md) · Task: [Bundle ingestion](../sprint/backlog/02-ingest-validation/backend/01-bundle-ingestion.md) · ✅ Done

**Event:** Task completed — Sprint 02 closed
**Files:** `apps/backend/app/router/bundles.py`, `app/service/{validation,hashing}.py`, `app/store/bundles.py`
> `POST /v1/bundles` is live and the frozen 501 placeholder was removed from `router/contract.py`.
> Content-type, size, and depth guards run before the payload is parsed, and depth is measured
> iteratively so hostile nesting is refused rather than blowing the stack. Every rejection
> carries its own stable code: unknown top-level key, dangling reference naming the missing
> resource, duplicate id, circular reference, malformed JSON, schema violation. Schema issues
> report the field path only — pydantic echoes offending values, and here those can be clinical
> text. Hashing normalises every timestamp to UTC and treats a naive one as UTC, so the same
> claim exported from two zones hashes identically; the idempotency key folds in engine and
> ruleset versions, so a version bump re-screens rather than serving a stale verdict.
> **Correction that shaped the design:** the first pass counted a billed line with no supporting
> reference as a completeness note, which made all five gold fixtures `VALID_WITH_NOTES` against
> their declared `expected_evidence_complete: true`. That would have lowered certainty and routed
> the phantom case to request-evidence — defusing the detector the system exists for. An
> unevidenced line is a finding; notes now cover only whole missing categories. A test locks it.
> Verified: `uv run pytest` → 204 passed (was 162); ruff clean across `app` and `tests` (the fix
> also reordered imports in 11 pre-existing files).

### 2026-08-31 · [Sprint 02 — ingest-validation](../sprint/backlog/02-ingest-validation/sprint.md) · Task: [Bundle ingestion](../sprint/backlog/02-ingest-validation/backend/01-bundle-ingestion.md) · ✅ Done

**Event:** Database layer bound, screen endpoint wired, Sprint 02 closed
**Files:** `apps/backend/migrations/`, `app/store/{tables,engine,registry,cases}.py`, `app/router/bundles.py`
> Postgres is live via Docker Compose and Alembic revision `3cf7d9b9fb28` created `ingestions`
> and `evidence_edges`. `migrations/env.py` reads the URL from `app.config` rather than
> `alembic.ini`, so the service and its migrations cannot point at different databases.
> `raw_payload` is TEXT, not JSONB: JSONB reorders keys and drops whitespace, destroying the
> exact form a re-derivation depends on. A test asserts the byte-for-byte round trip.
> `SqlBundleStore` and `SqlEdgeStore` join the in-memory pair behind the same protocols;
> `store/registry.py` picks once per process and falls back to in-memory when no database
> answers — the demo runbook needs an offline run and the frontend team has no Docker.
> Postgres check constraints refuse an out-of-enum status and a confidence outside 0..1, so the
> database backs up the types rather than trusting them.
> `POST /bundles/{id}/screen` was implemented here too, because the completeness notes had
> nowhere to travel without it: it screens against history drawn from earlier ingestions for the
> same participant and provider, creates a case, carries the notes onto it, and links the case
> back so a resubmission returns `existing_case_id`. Re-screening bumps the case version instead
> of forking a second case. The queue, dispositions, and audit trail stay with `04-review-slice`.
> Verified: 227 passed with Postgres · 215 passed and 12 skipped without it · ruff clean.

### 2026-08-31 · Sprint 02 follow-up · 🐛 Fixed + defect recorded

**Event:** Evidence edges now persist; clone-detection scope defect found and documented
**Files:** `apps/backend/app/router/bundles.py`, `docker-compose.yml`, `apps/backend/.env.example`
> Seeding a live database end-to-end surfaced two things the test suite could not.
> **Fixed:** `POST /bundles/{id}/screen` derived the evidence graph and threw it away — nothing
> was ever written to `evidence_edges`. It now persists the slice keyed by ruleset version.
> Re-seeded: 8 ingestions, 63 edges across 9 edge types.
> **Recorded, not fixed:** `history_for()` scopes to same participant *and* provider, which is
> right for repeat and unbundling but wrong for cloning — a per-provider pattern across
> different patients. The clone fixture therefore screens to `NO_OBSERVED_RISK` through the API,
> so one of four risk modes is inert on the live path. The suite missed it by passing
> `fixture.history` directly instead of going through the store. Fix is designed and recorded in
> the task file; deferred because it moves a privacy boundary.
> **Also:** the Postgres host port is now `${DB_PORT:-5432}` — 5432 was repeatedly taken, here by
> an editor's automatic port forwarding. This machine uses 55432.
> Verified: 227 passed · ruff clean.

### 2026-08-31 · [Sprint 01 — synthetic-data](../sprint/backlog/01-synthetic-data/sprint.md) · ✅ Done — Gate G3 met

**Event:** Sprint completed — generator, injectors, splits, and leakage controls
**Files:** `packages/data/`, `docs/canonical/decisions/ADR-0003-native-generator-instead-of-synthea.md`
> **Synthea replaced by a native generator, recorded in ADR-0003.** It is not installed, there is
> no Java Runtime here, and the adapter the data card describes would have discarded most of what
> Synthea provides — the whole billing layer that all four risk modes are defined over is
> constructed from scratch either way. The ADR also records what the proposal loses: the
> "Apache-2.0 Synthea" claim on slide 8 must be removed, not softened.
> **G3 measured, not asserted:** 1,120 bundles · 240 injections · 60 per mode across all four ·
> 300 participants · 8 providers · leakage margin **+0.0009** against a 0.10 tolerance. The whole
> pipeline is deterministic — corpus hash, labels, split digest, and data card all reproduce.
> **Two injectors were shipping false labels, and the invariant tests caught both.** Repeat copied
> the encounter at every difficulty, so the engine emitted `DUPLICATE_CLAIM_FINGERPRINT` while the
> label demanded the overlap reason — the engine was right. It now produces both shapes: verbatim
> resubmission for obvious, a second encounter for moderate and subtle. Clone dropped three subtle
> cases below the detector's reporting threshold, labelling as detectable something that was not;
> it now makes one substitution and refuses to inject into a note too short to absorb it.
> **The leakage probe is itself tested against a planted leak** — a probe that never fires proves
> nothing. Raw injector output does leak (`BND-00042-R173` announces its own injector);
> `strip_injector_traces` regenerates ids and reorders, and the probe confirms the tell is gone.
> The data card enforces all eleven required elements and the mandatory sentence verbatim.
> Verified: 47 tests in `packages/data` · backend 229 · domain 21.

### 2026-08-31 · [Sprint 04 — review-slice](../sprint/backlog/04-review-slice/sprint.md) · Backend: [case endpoints](../sprint/backlog/04-review-slice/backend/01-case-endpoints.md) + [disposition & audit](../sprint/backlog/04-review-slice/backend/02-disposition-audit.md) · ✅ Done

**Event:** Both backend tasks completed — six of seven endpoints now live
**Files:** `app/router/{cases,dispositions}.py`, `app/service/{case_query,disposition}.py`, `app/store/{audit,cases,tables}.py`, `migrations/`
> The vertical slice runs end to end against Postgres: ingest → screen → queue → detail →
> disposition → audit. All four risk modes fire, a stale write is refused, and the trail shows
> SCREENED · OPENED · DISPOSITION.
> **Append-only is enforced by a database trigger, verified live** — UPDATE and DELETE against
> `audit_events` are both refused with "audit_events is append-only" and the row survives. A
> reason is required at three layers: DTO, record construction, and a Postgres check constraint;
> the UI can be bypassed and internal callers can skip the DTO, so only the last catches
> everything. The audit event is written before the case moves, because an unexplainable state
> change is worse than a retryable failure.
> The queue carries no narrative text — asserted against the serialised response using four-word
> phrases, since reason sentences legitimately share common words with clinical notes. Queue and
> detail read the same catalog entry, so they cannot disagree about why a case was raised.
> `NOT_ASSESSABLE` stays distinct from `UNSUPPORTED`: requesting a document is a different act
> from questioning whether a service happened.
> `X-Actor-Role` is named as role simulation rather than dressed up as a token — enterprise IAM
> is out of scope and a credential-shaped header would invite the wrong assumption.
> Verified: 269 passed with Postgres · 255 passed and 14 skipped without it · ruff clean.

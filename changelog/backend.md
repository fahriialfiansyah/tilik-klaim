# Changelog — Backend

Append-only. Newest entry at the top. Agent and MCP tasks would also land here; this project has none.

---

### 2026-09-01 · [Sprint 04 — review-slice](../sprint/backlog/04-review-slice/sprint.md) · Task: [Ingest and seeded demo page](../sprint/backlog/04-review-slice/frontend/03-ingest-page.md) · ✅ Done

**Event:** Gold scenarios exported as demo payloads, with a drift guard
**Files:** `apps/backend/scripts/export_demo_samples.py`, `apps/backend/tests/test_demo_samples.py`
> The ingest screen offers five curated cases that load without an upload. They have to be *the
> same five* the gold fixtures describe, or the demo would show a system behaving differently
> from the one the tests cover — so they are generated rather than copied.
>
> Two things about the exported shape are deliberate. **The answer key is stripped:** a fixture
> carries `expected_reason_codes` and `expected_evidence_complete` beside the bundle, kept
> outside `CanonicalBundle` so no detector can reach them, and shipping them to a browser would
> put the expected answer one devtools panel away from anyone watching the demo. **The history
> comes along:** three of the five scenarios are cross-claim patterns that screen to nothing
> without their prior bundle — a sample exported without it would ingest cleanly and prove the
> opposite of what it is there to show.
>
> Six tests guard all of it, and they were checked by breaking a sample and watching them fail.
> No API change: the ingest screen uses `POST /v1/bundles` and `POST /v1/bundles/{id}/screen`
> exactly as they stand, and the demo/reset route stays sprint 07's to design.
>
> Backend 312 passed.

---

### 2026-09-01 · [Sprint 04 — review-slice](../sprint/backlog/04-review-slice/sprint.md) · Task: [Case detail, evidence trace, and disposition panel](../sprint/backlog/04-review-slice/frontend/02-detail-kasus.md) · ✅ Done

**Event:** Case detail extended so the screen's binding display rules can actually be met
**Files:** `apps/backend/app/service/case_sources.py`, `apps/backend/app/service/case_query.py`, `apps/backend/app/dto/{cases,common,dispositions}.py`, `apps/backend/app/router/cases.py`, `apps/backend/scripts/seed_dev.py`, `packages/domain/src/tilik_domain/reasons.py`
> Four additive changes to `GET /v1/cases/{id}`. Every one adds a defaulted field and changes no
> existing wire model, so the frozen contract and the committed fixtures both still hold. Each
> exists because a spec'd display rule could not be met correctly in the client.
>
> 1. **Counter-evidence now carries its sentence.** The rules already wrote it — "*Bundel ini
>    hanya memuat bukti yang ikut terkirim. Tidak ditemukannya catatan di sini bukan bukti bahwa
>    layanan tidak diberikan*" is the sentence that keeps a missing record from reading as a
>    missing service — and the DTO was dropping it, shipping only the bare resource references.
>    Widget 13 was therefore a resource id under a heading, with no argument in it at all.
>    `counter_evidence_notes` carries note plus refs; `counter_evidence` stays as it was.
> 2. **A source index, so every evidence reference opens.** `sources` resolves each reference a
>    reason cites — and each one the episode timeline points at — to one of four states:
>    `PRESENT`, `RELATED_BUNDLE`, `NOT_STORED`, `MISSING`. Only the last is a defect, and it is
>    *recorded* rather than omitted: dropping an unresolvable reference renders as a shorter
>    list, indistinguishable from a reason that simply cited less. `RELATED_BUNDLE` is reduced to
>    non-identifying fields — never a peer participant's narrative or token, which
>    `docs/canonical/07_privacy_threat_model.md` names as the exposure route for clone
>    comparisons.
> 3. **Comparisons compare something.** `fields` was built from the reason's own component
>    scores with the same value on both sides and `matches` hard-coded true — a comparison in
>    which nothing could ever differ. Repeat-billing pairs are now compared claim to claim
>    (visit, care type, total, line count, submission time, episode) with a real overlap window;
>    clone pairs are compared by document shape only.
> 4. **`expected_support` on the reason catalog.** `required_evidence` says what the *reason*
>    needs to be well formed; the screen needs what should have stood behind the *billed line*.
>    Rendering the first as "bukti yang diharapkan" reported that everything expected had been
>    found — on a phantom case, whose entire finding is an absence.
>
> **Reasons are now ordered strongest-first in the response,** once, so the queue row, the case
> header, and the reason cards cannot disagree. Rule registration order is fixed for
> reproducibility and says nothing about what a person should read first; a similarity reason
> registered ahead of a deterministic conflict would have led every surface while the band came
> from the reason underneath it.
>
> **`scripts/seed_dev.py` cleared bundles but not cases.** The previous run's cases survived,
> pointing at ingestion ids that had been deleted, so the detail endpoint answered with empty
> `lines` and `timeline`. The screen rendered a case with no billed lines on it, from a database
> that looked freshly seeded. It now empties every store.
>
> **`docs/api/openapi.json` regenerated, and `scripts/export_openapi.py` added so it stops
> drifting.** It had been written once at the contract freeze in sprint 02 and never again, so
> two sprints of implementation had passed it by: it still described `ReasonDto` without its
> counter-evidence notes and `/v1/cases` with ingest-only error codes that endpoint never
> returns. A spec that has quietly stopped matching the service is worse than none — a generated
> client compiles against it and fails at runtime. The frozen contract is unaffected: it lives in
> `tests/test_api_contract.py` and the committed fixtures, both of which read the live app.
>
> Ten new tests; backend 295 passed, domain 23 passed.

---

### 2026-09-01 · [Sprint 04 — review-slice](../sprint/backlog/04-review-slice/sprint.md) · Task: [Review queue page](../sprint/backlog/04-review-slice/frontend/01-antrean-review.md) · ✅ Done

**Event:** Queue filtering and sorting extended for the review UI
**Files:** `apps/backend/app/router/cases.py`, `apps/backend/app/service/case_query.py`, `apps/backend/tests/test_case_endpoints.py`
> `GET /v1/cases` gained `mode` and `sort`/`order`. Both are additive query parameters that
> change no wire model, so the frozen contract still holds. They exist because the queue's
> spec'd mode filter and four sort keys are not implementable correctly in the client: the
> response is paginated, so narrowing or re-ordering it there would act on one page and
> silently ignore every match on the others.
>
> **The band sort ignores `order` by design.** It is the product's answer to "what do I review
> next", and inverting it would put `NO_OBSERVED_RISK` at the top of a work list — a reading
> the system is not entitled to offer. An unknown sort key is refused with 422 rather than
> falling back to the default, because a wrong order that looks right is worse than an error.
> **Three defects found in code review of this same change, all fixed:**
>
> 1. **The queue and the case detail disagreed about evidence completeness on every case.**
>    `evidence_completeness()` fell back to the count of *unsupported* lines when no line count
>    was passed, so `supported_lines` was zero by construction: a fully supported case reported
>    "0 of 0 lines" and the queue rendered it as having nothing billed at all, while the detail
>    — which passes the real count — showed 2 of 2. The count is now recorded on the case at
>    screening (`billed_line_count`, migration `d1a7c3e50f42`), which also keeps the queue from
>    reading 25 bundles to build one page.
> 2. **`sort=age&order=desc` returned the newest case first.** Age is displayed as
>    `now - screened_at`, which moves opposite to the timestamp being sorted, so "descending"
>    meant "largest" on the amount column and "smallest" on the age column — same control,
>    opposite meaning. `_sort_value` now sorts on the displayed quantity.
> 3. **Search was applied client-side to an already-paginated page**, so a case whose identifier
>    sat on page 2 was unreachable: page 1 came back empty and the empty state offered only
>    "clear the filters". `search` is now a query parameter narrowing the whole queue, like
>    every other filter.
>
> Verified: 285 tests passing (was 269), ruff clean, alembic head `d1a7c3e50f42`.

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

### 2026-09-01 · [Sprint 01 — synthetic-data](../sprint/backlog/01-synthetic-data/sprint.md) · Fix: published artifacts did not join · 🔧 Code done, regeneration pending

**Event:** `write_artifacts` published the corpus from before the injector scrub
**Files:** `packages/data/src/tilik_data/{leakage,pipeline}.py`, `packages/data/tests/{test_artifacts,test_leakage}.py`
> `write_artifacts` wrote `result.corpus.bundles` — the corpus **before**
> `strip_injector_traces` ran. So `corpus.json` still carried the injector tell (120 of 1,120
> ids shaped like `BND-00008-U798`), `split.json` held the renamed ids and shared **zero**
> overlap with it, and `manifest.corpus_hash` hashed a corpus nobody published. The leakage
> probe reported a pass because it ran on `cleaned`, which never reached disk. `write_artifacts`
> had no test at all, which is why this survived from Sprint 01 to Sprint 05.
> `BuildResult` now carries **only** the scrubbed bundles and the labels renamed to match, so
> reaching past the scrub is unrepresentable rather than merely fixed.
> **The scrub itself was incomplete.** It rewrote `bundle_id` and nothing else, leaving
> `CLM-00008-U798` and `LN-00008-1-U798` inside the record saying the same thing one level down
> — invisible to a probe that only reads bundle ids, and contradicting Sprint 01's own note that
> it "regenerates every identifier". It now rewrites every injector-marked identifier through
> one rename map, and the labels are carried through that same map so ground truth still joins.
> `tests/test_artifacts.py` asserts on the **files**, not the in-memory result: the three files
> share one id space, every label target and evidence ref resolves, the manifest describes the
> corpus actually written, and no published string anywhere carries an injector suffix.
> **`test_set_digest` is unchanged** by the fix — `ed903a4c39656e…` before and after, along with
> every partition count, the split membership, and the leakage margin. The frozen split is not
> re-frozen; only `corpus_hash` moves, and it moves because the old value described a corpus
> that was never written. **Regeneration awaits the owner's decision** (`docs/HANDOVER.md` § 7).
> Verified: data 57 passed (was 47) · backend 312 · domain 23 · model 71 · web 91 · tsc clean · ruff clean.

### 2026-09-01 · [Sprint 05 — ranking-models](../sprint/backlog/05-ranking-models/sprint.md) · Backend: [similarity & anomaly baselines](../sprint/backlog/05-ranking-models/backend/01-similarity-anomaly.md) · ✅ Done

**Event:** `packages/model` created — ranking baselines behind a single call site
**Files:** `packages/model/src/tilik_model/{feature_schema,features,measures,similarity,anomaly,calibration,ranking,persistence,dataset,model_card,version}.py`, `packages/model/tests/`
> 21 features across the six families the canonical model card names, a character n-gram TF-IDF
> similarity baseline, and an Isolation Forest over robustly scaled peer features. The
> aggregation is the specified `max(deterministic, calibrated_similarity, calibrated_anomaly)`
> with all three caps, applied in one place and recorded by name on every result.
> **The caps are ordered deliberately.** The similarity ceiling is applied to the *component*,
> so no combination of inputs lets text lift a case into a high band. The duplicate-fingerprint
> floor raises an exact duplicate — a floor on queue position, nothing more. The
> incomplete-bundle step-down comes **last**, because it is the cap that protects against a false
> accusation and must override the other two; it never drops a case below *needs context*, so a
> raised case stays visible while ceasing to be urgent.
> **The leakage probe re-identifies the whole corpus and refits the peer profile on it**, then
> asserts the feature table does not move. That is stronger than checking no injector field was
> copied into a column: it proves no feature reads an identifier at all. A companion test plants
> an id-reading feature and confirms the probe catches it.
> **Thresholds are fitted on validation only, and `BandCalibration.fit` refuses any other
> partition by name** rather than trusting the caller. A statistical score can never reach
> `DETERMINISTIC_CONFLICT`, and the model emits no disposition other than *request evidence*.
> **Training would have seen test participants.** The split groups by
> `(participant, facility, time block)`, so a participant can appear in two partitions at another
> facility or in another month: 125 of 140 test participants also appear in train, and 299 of 674
> training bundles are contaminated. Rather than re-cut a split announced as frozen, the
> contamination is dropped on the training side and the count reported.
> **A band raised only by a model score has no reason to show a reviewer.** Suppressing those
> would be a fourth cap the canonical card does not specify, so each is flagged
> `explained_by_reasons: false` and named in the model card's limitations; Sprint 06 decides.
> Nothing outside the package imports any module in it and no score reaches a wire model, so the
> sprint's removal clause stays a single revert.
> Verified: model 71 passed · backend 312 · domain 23 · data 57 · web 91 · tsc clean · ruff clean.

### 2026-09-01 · [Sprint 06 — evaluation-report](../sprint/backlog/06-evaluation-report/sprint.md) · Backend: [evaluation runner](../sprint/backlog/06-evaluation-report/backend/01-evaluation-runner.md) · ✅ Done

**Event:** `evaluation/runner` built; the last 501 endpoint is now live — all seven are implemented
**Files:** `evaluation/runner/*.py`, `evaluation/tests/`, `apps/backend/app/service/evaluation_artifacts.py`, `apps/backend/app/router/evaluations.py`, `app/config.py`, `app/main.py`; `app/router/contract.py` deleted
> One command rebuilds every metric, table, and chart: `uv run python -m runner.run --build …`.
> Four baselines (B0 random, B1 rules-only, B2 statistical-only, hybrid), the seven primary
> metrics, bootstrap intervals, five breakdown dimensions, and case reports for manual review.
> **Gates run before any metric.** `preflight.py` refuses a corpus whose ids still carry an
> injector suffix, refuses a demo fixture in any partition, and halts on the leakage probe. A
> metric computed on a leaking corpus is a number someone might believe, and one that exists
> gets quoted.
> **`metrics.json` carries no run id and no timestamp**, because it is hashed and compared
> across runs; anything that legitimately differs between two runs of one commit is in the
> manifest. Latency is written but deliberately *not* hashed — it measures the machine, not the
> method, and hashing it would make the reproducibility check permanently false.
> **A near-miss.** Evidence-reference validity first reported 39 of 140 displayed references as
> unresolvable. All 39 were clone reasons pointing at a *peer* note — another participant's, at
> the same facility, which is exactly where a clone reason must point. The checker was wrong, not
> the detector. Left as measured, the obvious response would have been to "fix" a working
> detector. Validity is 1447/1447 once peer documents are in the resolvable set.
> **`GET /v1/evaluations/{run_id}` reads artifacts and computes nothing.** A metric producible by
> an HTTP request is a metric produced more than once. `latest` is a reserved path *value*, not a
> new endpoint, so the frozen contract is intact. Undefined values are **omitted** rather than
> zero-filled: the wire model's floats cannot carry a null, and a zero would claim a measurement
> nobody made. `app/router/contract.py` is deleted — it held only placeholders and there are none
> left.
> **Rehearsal figures only** — the official run waits on the `packages/data/build/` regeneration
> decision, and `load_build` correctly refuses the current artifacts. Against a scratch corpus the
> hybrid's macro F1 is *identical* to rules-only (0.6510): it detects nothing the rules do not.
> What moves is ranking — PR-AUC 0.7122 → 0.8440, precision at the review budget 0.9565 → 1.0000
> — bought at slightly more false positives per 100 clean claims. If that holds, the incremental
> value is prioritisation, not detection. No tuning was done.
> Verified: evaluation 47 passed · backend 322 passed (was 312) · model 71 · data 57 · domain 23 ·
> web 104 · tsc clean · ruff clean · playwright 14 passed in 10.0s.

### 2026-09-01 · [Sprint 07 — demo-hardening](../sprint/backlog/07-demo-hardening/sprint.md) · Backend: [demo reset & health](../sprint/backlog/07-demo-hardening/backend/01-demo-reset-and-health.md) · ✅ Done

**Event:** One-command demo reset, and a readiness check that answers "will the demo work"
**Files:** `apps/backend/scripts/demo_reset.py`, `app/service/demo_state.py`, `app/router/health.py`, `tests/test_demo_readiness.py`
> `uv run python scripts/demo_reset.py` empties every store together, re-seeds the five gold
> scenarios, and **verifies** — 0.2–0.4 s, idempotent. A seed that "succeeded" while the phantom
> fixture screened to nothing exits non-zero here instead of being discovered on stage.
> **`/healthz` deliberately does not fail when the database does.** `railway.json` probes that
> path; a 5xx there would restart the container in a loop precisely when the database is already
> struggling, and the backend is designed to run with no database at all so the demo can be
> rehearsed offline. Liveness stays `200 · ok`; the new `readiness` block reports database
> reachability, seeded-case count, whether the runbook's ideal case is present *and untouched*,
> and a named problem for each thing wrong. `--check` reads that block and exits non-zero — which
> is where "fails loudly" belongs, because a pre-demo check is read by a person and a container
> probe is not.
> **Readiness checks the demo case, not a row count.** Five rows is not a working demo: a case
> someone already dispositioned is a different demo, and
> `test_an_opened_demo_case_makes_the_system_not_ready` holds that line.
> Verified: backend 330 passed (was 322) · ruff clean · playwright 17 passed in 12.6 s.

### 2026-09-01 · Cleanups from [`docs/HANDOVER.md`](../docs/HANDOVER.md) § Owed · ✅ Done

**Event:** The suite stopped wiping the dev database, and the comparison drawer got its link
**Files:** `tests/conftest.py`, `tests/test_test_database_isolation.py`, `app/store/bundles.py`, `app/service/{case_sources,case_query}.py`, `app/router/cases.py`, `tests/test_case_detail.py`
> **`uv run pytest` no longer empties the developer's database.** Every store is cleared around
> every test and the stores are bound to whatever `DATABASE_URL` points at, so the suite had been
> emptying seeded dev data as a side effect — an indirect and expensive failure: the seed looked
> fine, the screens came up blank, and the cause was a test run somebody had done twenty minutes
> earlier. `tests/conftest.py` now creates and migrates `tilik_klaim_test` in `pytest_configure`,
> **before any test module is imported**, because several evaluate `skipif(not use_database())`
> at *collection* time and redirecting later would leave those decisions made against the wrong
> database. An unreachable server or a failed `CREATE DATABASE` changes nothing and the
> integration tests skip exactly as before — running without a database is a supported
> configuration, not a fault.
> `test_test_database_isolation.py` is the alarm: a redirect that quietly stops working is worse
> than none, because the trap returns without the warning that used to be in the handover.
> **`ComparisonCandidate.candidate_case_id` is no longer always null.** `BundleStore` gained
> `case_id_for_bundle`, which returns the identifier alone rather than the record — a drawer
> needs a link, not another participant's submission, and an API that could hand back the whole
> record is one somebody will eventually use that way. Only the repeat-billing pair is resolved:
> its candidate is the same participant's earlier claim at the same facility, so opening it
> crosses nothing. Two `null` cases are **correct and now asserted**: an accepted-but-never-
> screened candidate has no case, and a clone candidate is another participant's note, which this
> layer is handed without the submission behind it.
> Verified: backend 337 passed (was 330) · web 107 (was 104) · ruff clean · playwright 17 · the
> dev database survived a full `pytest` run with its five seeded cases intact.

### 2026-09-01 · Corpus regenerated · Sprint 06 official run · ✅ Done

**Event:** `packages/data/build/` regenerated with the owner's go-ahead; sprint 06 evaluated once against the frozen test set
**Files:** `packages/data/build/*`, `evaluation/artifacts/run-20260901T110000Z/`, `docs/artifacts/failure-modes.md`
> `test_set_digest` came back **unchanged** (`ed903a4c39656e…`), so the frozen split was not
> re-frozen and sprint 01's gate evidence survives. Only `corpus_hash` moved, from
> `db694e6851c9…` to `1ff95898c696…`, and it moved because the old value described a corpus that
> was never written to disk. The artifacts now join fully: 1120/1120 split ids present, 352/352
> label targets resolve, **0 identifiers carrying an injector suffix**.
> **The official run measured what the rehearsal predicted, and the result is not a win.**
> Per-mode metrics are **identical across all four modes** between rules-only and hybrid: the
> statistical layer detects nothing the rules do not. Precision at budget rose 0.9565 → 1.0000
> but the 95% intervals overlap ([0.870, 1.000] vs [0.913, 1.000]); recall@K differs by one case.
> PR-AUC shows a real gap (0.7122 → 0.8440) but is not the acceptance criterion and carries no
> interval. **Sprint 05's removal clause is live**, and the decision belongs to the sign-offs.
> **Failure-mode write-up drafted.** Clone detection is the false-positive engine — precision
> 0.1154 at recall 1.0000, flagging 130 of 228 claims to catch 15, with 24 of 25 reviewed false
> positives raising `NEAR_DUPLICATE_DOCUMENTATION` alone. And **all 9 false negatives are the
> earliest bundle of their injected pair, with empty history** — verified 9 of 9. Repeat and
> unbundling label *both* bundles, but at the first one's submission time the sibling does not
> exist, so the rule cannot fire. Recall for those modes is understated by construction.
> Only 9 false negatives exist, not the 25 the plan asks to review; that is reported as-is rather
> than padded.

### 2026-09-01 · Readiness caught a live "the demo would have failed" condition · ✅ Done

**Event:** The API served in-memory state for hours while Postgres was up and reachable
**Files:** `app/service/demo_state.py`, `tests/test_demo_readiness.py`
> The running API reported `database_reachable: true` and `persistence: "in-memory"`. It had
> started while Postgres was still coming up, chose the in-memory stores, and `use_database()`
> caches that answer for the life of the process — deliberately, so two stores can never disagree
> about where an ingestion lives. The consequence: `demo_reset.py` wrote five cases to Postgres
> and the API kept serving three from memory. Two E2E specs failed and looked like a regression
> in code that was fine.
> **Re-seeding does not fix it; only a restart does**, and the check now says exactly that.
> This is the failure sprint 07 exists to prevent, found in the wild by the check built for it.
> Verified: backend 338 passed (was 337) · playwright 17 passed after the restart · ruff clean.

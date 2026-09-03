# HANDOVER — TilikKlaim

State snapshot for picking this up in a fresh session.
Pair with [`sprint/01-sprint-planning.md`](../sprint/01-sprint-planning.md),
`changelog/{backend,web}.md`, `docs/canonical/`, and [`qa/MANUAL-QA.md`](./qa/MANUAL-QA.md).

- Repo: `/Users/fahrialfiansyah121gmail.com/Documents/HEALTHKATHON-2026/tilik-klaim`
- Branch: `development` · 18 commits, HEAD `3c661e7`, tree clean except `scripts/dev.sh`
  (the owner's own in-progress `--free-ports` flag). **In sync with a PUBLIC GitHub remote**
  (`github.com/fahriialfiansyah/tilik-klaim`) — do not push without asking.
- Companion: [`CONTINUE-PROMPT.md`](./CONTINUE-PROMPT.md) boots a fresh session into the next
  task; [`qa/MANUAL-QA.md`](./qa/MANUAL-QA.md) is what the owner checks by eye.
- Goal: a claim-evidence integrity layer that screens synthetic SATUSEHAT-shaped JKN claim
  bundles for four facility risk patterns and requires a logged human disposition. Healthkathon
  2026 entry, category *Efisiensi Risiko pada Fasilitas Kesehatan*; proposal due **19 September
  2026** (internal upload target 18 Sep).

---

## 1. Orientation (read first)

**The ethical core is encoded in types and asserted by tests — it is not a style preference.**
The system reports "risiko atau anomali yang perlu ditinjau". It never states fraud, never
rejects a claim, never moves a payment, never imposes a sanction, never changes a code, and never
decides medical necessity. Tests enforce this: `test_no_rule_ever_uses_the_word_fraud` scans
reason text, and `test_no_action_triggers_payment_rejection_or_sanction` walks the disposition
service's **syntax tree** (not its text — the module docstring names those words precisely to rule
them out).

**One distinction carries more weight than any other.** An incomplete record and a
billed-but-unevidenced service look identical at the schema level. Conflating them is how this
system would manufacture a false accusation. So:

- ingestion returns three states, and `VALID_WITH_NOTES` is *not* a softer `INVALID` — it still
  screens, and the ingest screen's tests assert exactly that;
- **a billed line with no supporting reference is a finding, not a completeness note.** An
  earlier version recorded it as incompleteness, which lowered certainty and would have defused
  the phantom detector entirely;
- an incomplete bundle *lowers* the band and routes to `REQUEST_EVIDENCE`, never toward
  `CONFIRM_ANOMALY`;
- case detail keeps `NOT_ASSESSABLE` distinct from `UNSUPPORTED`.

**Cloning is a per-provider pattern across different patients**, not per-patient.
`history_for()` scopes to same participant + provider (correct for repeat and unbundling);
`peer_documents_for(provider_id)` crosses the wider boundary and returns **only `DocumentRef`** —
notes cross, whole bundles never do.

**Three doc layers, one writer per fact.** `docs/canonical/` is read-only (change only via a new
ADR); `brief/` is the product blueprint in Indonesian; `sprint/` holds plans and task files in
English. Never restate a fact across layers.

**No LLM anywhere in the risk path, and no agents** (ADR-0002). The Workforce Manifest holds only
`be_service` and `fe_shell`. This binds sprint 05 directly: no LLM and no GNN in the score.

**Sprint 05's kill criterion is a designed outcome, not a failure mode.** If the hybrid adds no
measurable value over rules-only, the ML layer is **removed** and TilikKlaim ships rules-only.
`docs/canonical/01_product_decision.md` says so explicitly: *"this is not a product kill."*
Reporting that honestly is stronger evidence of method than a marginal gain would be — so do not
tune until something looks better.

## 2. Done so far

| Sprint | Gate | Status | Evidence |
|---|---|---|---|
| 00 — foundation | — | ✅ Done | both apps scaffolded and green |
| 01 — synthetic-data | G3 · 2 Sep | ✅ **Done** | 1,120 bundles · 240 injections · leakage margin +0.0009 · artifacts regenerated 1 Sep, `test_set_digest` unchanged |
| 02 — ingest-validation | G4 · 5 Sep | ✅ Done | `POST /v1/bundles` + screen endpoint live on Postgres |
| 03 — evidence-rules | G4 · 5 Sep | ✅ **Done, gate met early** | 10 edge types, 4 risk modes, all caps enforced |
| 04 — review-slice | G5 · 9 Sep | ✅ **Done, gate met early** | all three screens live on the real API; 14 Playwright specs green in 9.8 s |
| 05 — ranking-models | G6 · 12 Sep | ✅ **Done** | `packages/model` built, 71 tests; incremental value measured in 06 |
| 06 — evaluation-report | G6 · 12 Sep | 🚧 **Official run done** | only the three sign-offs remain; **removal clause is live** |
| 07 — demo-hardening | G8 · 17 Sep | 🚧 **Nearly done** | only the 1080p recording + 3-min rehearsal remain |
| 08 — evidence-workspace | G8 · 17 Sep | ✅ **Done 3 Sep** | `/cases/:id` is an Evidence Workspace (ADR-0004); frontend-only, no contract change |
| 09 — case-briefing | G8 · 17 Sep | ✅ **Done 3 Sep** | Bounded read-only briefing outside the risk path (ADR-0005); **off by default**; eighth endpoint; no real model called yet |

**Verified immediately before writing this:**

```
backend 403 · domain 23 · data 57 · model 71 · evaluation 47 · web 184 · playwright 24
tsc clean · ruff: All checks passed · alembic head d1a7c3e50f42     (re-measured 3 Sep 2026)
```

**3 Sep:** two ADRs are drafted and one is landed. [ADR-0004](canonical/decisions/ADR-0004-evidence-workspace.md)
(Evidence Workspace) is **implemented**. [ADR-0005](canonical/decisions/ADR-0005-bounded-case-briefing.md)
(bounded read-only Case Briefing, outside the risk path) is **implemented too**, on the owner's
explicit approval, with its recorded deviation: sprint 06 still reads 🚧 while its three human
sign-offs are outstanding — flip it when they land. **`BRIEFING_ENABLED` is `false`; no real
model has been called from this repo.** Turning it on is `apps/backend/.env` (`OPENROUTER_*`)
and a deliberate look at the result. The full plan for both is
`docs/plans/2026-09-03-evidence-workspace-and-case-briefing.md`.
**One environment trap found:** `uv sync` drops the editable `tilik-domain` (not declared in
`apps/backend/pyproject.toml`; the README omits it). Restore with
`(cd apps/backend && uv pip install -e ".[dev]" -e ../../packages/domain)`. All three files sit
under gitignored `docs/` and were `git add -f`'d, like ADR-0001..0003 before them.

**A trap worth knowing before you debug anything.** If `/healthz` reports
`database_reachable: true` with `persistence: "in-memory"`, the API started before Postgres was
up and cached that choice for the life of the process. `demo_reset.py` then writes to Postgres
while the API serves memory, screens look plausibly wrong, and E2E specs fail as if the code
regressed. **Restart the API**; re-seeding does not help. The readiness block says so.

`packages/data` rose 47 → 57 (the artifact writer finally has tests) and `packages/model` is new.
Add it to the sweep: `(cd packages/model && uv run pytest)`.

**All seven frozen endpoints are live.** Sprint 06 filled the last one;
`test_every_frozen_endpoint_is_now_implemented` guards against a placeholder being left in front
of working behaviour, and `app/router/contract.py` is gone because it held only placeholders.

**All three operator screens are complete**, each verified in a browser rather than only by test:
`/` (Antrean Review), `/cases/:id` (Detail Kasus — 27 widgets, five binding display rules), and
`/ingest` (Ingest / Demo — 11 widgets, three validation states), and `/evaluation` (Audit &
Evaluasi — 9 widgets, display-only, four states). The full path — ingest → screen → queue → detail →
disposition → audit — runs end to end against real Postgres with all four risk modes firing and a
stale write refused.

**Manual QA is in [`qa/MANUAL-QA.md`](./qa/MANUAL-QA.md)** with 30 screenshots across three
folders: five queue states, sixteen case-detail states (including the stale-version banner, the
save failure, the not-found page and the loading skeleton), and nine ingest states (all three
validation outcomes, both refusal paths, the identical-bundle notice, the service failure).
`docs/` is gitignored, so those screenshots live locally only.

**Defects worth carrying forward — every one was found by opening the page or reading the actual
payload, not by the compiler or the test suite:**

| Defect | Why it was invisible |
|---|---|
| Queue and case detail disagreed about evidence completeness on **every** case | `evidence_completeness()` fell back to the count of *unsupported* lines, so `supported_lines` was 0 by construction. Fixed by recording `billed_line_count` at screening (migration `d1a7c3e50f42`) |
| **Every** Button lost its text colour | `tailwind-merge` read `text-body-lg` as a *colour* and dropped `text-brand-on`. Primary buttons rendered at **2.5:1**. `cn()` now declares the project's type scale in `src/lib/utils.ts` |
| Counter-evidence reached the screen as a bare resource id | The rules wrote the sentence; the DTO shipped only the refs. Widget 13 was a heading with no argument under it |
| The comparison drawer compared a number to itself | `fields` came from the reason's own component scores, left = right, `matches` hard-coded true |
| "Expected evidence" reported everything found on a phantom case | `required_evidence` (what the *reason* needs to be well formed) was rendered where `expected_support` (what should back the *billed line*) belonged |
| Focus fell to `<body>` when any drawer closed | Radix restores focus to `DialogTrigger`, which this app never uses, and `preventDefault()`s the browser's own restore. Invisible with a mouse |
| A refused bundle was reported as a broken service | The API refuses along two paths — `4xx` before parsing, `200` + `INVALID` after — and a plain `catch` offered a retry on a file that would be refused identically every time |
| `seed_dev.py` cleared bundles but not cases | Orphan cases pointed at deleted ingestions, so case detail answered `lines: []` on data that looked freshly seeded |
| `docs/api/openapi.json` sat two sprints stale | Regenerating it was a manual step nobody remembered. `scripts/export_openapi.py` now exists; run it after any router or DTO change |

The lesson generalises, and is why `qa/MANUAL-QA.md` exists: **measure the rendered page and the
actual payload, not the source you just wrote.**

## 3. Environment

- **Python**: `uv` manages 3.11. System Python is 3.9 and too old. Never activate a venv
  manually — `uv run` handles it.
- **Node**: 20.x for `apps/web`. **Playwright** (`@playwright/test` + Chromium) is installed.
- **Postgres 16** via Docker Compose, container `tilik_klaim_db`, **host port 55432** on this
  machine (`DB_PORT` in the repo-root `.env`; the compose default is still 5432 for teammates).
- **Docker Desktop dies often here.** `open -a Docker`, then wait for `docker info` to answer.
- Secrets: `apps/backend/.env` (gitignored), template in `.env.example`. Local credentials are
  `tilik` / `tilik` / `tilik_klaim` — synthetic data only, nothing sensitive.
- **The backend runs with no database at all**, falling back to in-memory stores. That is a
  requirement, not a convenience: the demo runbook needs an offline run and the frontend team has
  no Docker. Without Postgres, 14 integration tests `skip` — they do not fail.
- **ML dependencies are already declared.** `apps/backend/pyproject.toml` carries
  `scikit-learn>=1.5` and `pandas>=2.2`. `packages/model/` is an empty placeholder holding only a
  README; sprint 05 writes its `pyproject.toml` — copy the shape of `packages/data/pyproject.toml`,
  which shows the `[tool.uv.sources]` editable-path pattern for depending on `tilik-domain`.

## 4. Build / run / test / verify

```bash
# --- everything at once (API + Web + Postgres + migrations; Ctrl-C stops all) ---
./scripts/dev.sh --db
(cd apps/backend && uv run python scripts/seed_dev.py)   # once, after the DB is up
(cd apps/backend && uv run python scripts/demo_reset.py) # before a demo or the E2E suite
(cd apps/backend && uv run python scripts/demo_reset.py --check)  # readiness, exits non-zero

# --- or piecemeal ---
open -a Docker && sleep 25                    # macOS; daemon is flaky here
docker compose up -d db                       # ~10s to report healthy
(cd apps/backend && uv run alembic upgrade head)
(cd apps/backend && uv run uvicorn app.main:app --reload --port 8000)
(cd apps/web     && npm run dev)              # :3000, proxies /v1 to :8000

# --- the six verify commands; run ALL after every change, and report the counts ---
(cd apps/backend    && uv run pytest)                 # expect 312 passed
(cd packages/domain && uv run pytest)                 # expect 23 passed
(cd packages/data   && uv run pytest)                 # expect 47 passed
(cd apps/web        && npx tsc --noEmit)              # expect silence
(cd apps/web        && npm test)                      # expect 91 passed (vitest)
(cd apps/backend    && uv run ruff check app tests)   # expect "All checks passed!"

# --- end-to-end (needs API + web up and a FRESH seed) ---
(cd apps/backend && uv run python scripts/seed_dev.py)
(cd apps/web && npm run test:e2e)             # expect 14 passed, ~10s

# --- generated artifacts: regenerate after any change to what they describe ---
(cd apps/backend && uv run python scripts/export_openapi.py)        # docs/api/openapi.json
(cd apps/backend && uv run python scripts/export_demo_samples.py)   # apps/web/public/samples/
(cd packages/data && uv run python -m tilik_data.pipeline --out build)

# --- DBeaver / any SQL client ---
# host localhost · port 55432 · db tilik_klaim · user tilik · password tilik
```

**How a visible change is verified:** load the affected screen at <http://localhost:3000> against
a seeded database and look at it. Screenshots of every state go to `docs/qa/<date>-<screen>/` with
a numbered click-through appended to `docs/qa/MANUAL-QA.md` — the owner checks those by eye in the
morning, which is the whole point of the folder.

## 5. Conventions & gotchas

**Conventions.** Conventional Commits, one line, no watermark trailer. Code identifiers in
English, user-facing text in Indonesian. Backend code in
`apps/backend/app/{router,service,dto,store}/`; shared types in `packages/domain`; generator in
`packages/data`; models in `packages/model`; frontend domain components in
`apps/web/src/features/{domain}/{feature}/components/` — **never** bare `src/components/`;
navigation only in `src/config/menu/*`; bounded scroll regions use `PerfectScrollArea`. Immutable
models (`frozen=True`), files 200–400 lines, functions under 50, explicit error handling, no magic
numbers. TDD: write the failing test first. When a task completes: tick every `## TODOs` box, set
the top-of-file `**Status:** ✅ Done` (the header is the source of truth), and append to
`changelog/{backend,web}.md`. Completed sprints stay in `sprint/backlog/` in this repo — sprints
00–04 all did; flip the status in `sprint/01-sprint-planning.md` rather than moving folders.

**Tailwind v4 is CSS-first — there is no `tailwind.config.ts`.** The theme is an `@theme inline`
block in `apps/web/src/styles/app.css` pointing at `src/styles/tokens.css`, a literal `cp` of
`design/tokens.css`. **Tailwind's default colour palette is deleted** (`--color-*: initial`), so
`bg-red-500` produces nothing on purpose: red-only-for-conflict and green-only-for-completed-
actions are enforced by the build rather than by review. Use the semantic names (`bg-card`,
`text-ink`, `border-line`, `bg-brand`, `text-band-conflict`, `bg-notice-bg`, `text-done`).

**Traps hit across these sessions, with the fix:**

| Trap | Fix |
|---|---|
| ~~`uv run pytest` empties the dev database~~ — **fixed.** `tests/conftest.py` creates and migrates `tilik_klaim_test` in `pytest_configure`, before any module is imported (several evaluate `skipif(not use_database())` at collection time) | nothing to do; `test_test_database_isolation.py` fails loudly if the redirect ever regresses. No database reachable still means the integration tests skip |
| Port 5432 gets stolen by **VS Code's automatic port forwarding**; symptom is a healthy container but *password authentication failed for user "tilik"* | `lsof -nP -iTCP:5432 -sTCP:LISTEN`; this machine uses `DB_PORT=55432` |
| Orphaned dev servers hold :3000/:8000 after a terminal closes | `./scripts/dev.sh --free-ports` (the owner's uncommitted addition), or `pkill -f rsbuild` / `pkill -f "uvicorn app.main:app"` |
| `ruff` B008 on `Depends()` in argument defaults | use `Annotated[T, Depends(f)]` |
| `SourceType` has no `EMR`/`BILLING` — only `SYNTHETIC_GENERATOR`, `UPLOADED_BUNDLE`, `GOLD_FIXTURE` | correct as-is: provenance records how a record entered *this* system |
| `ClaimStatus` has no `SUBMITTED` (`DRAFT`/`ACTIVE`/`CANCELLED`/`ENTERED_IN_ERROR`) | use `ACTIVE` |
| Service-level tests passing `fixture.history` directly **hid a live defect** | test cross-claim behaviour at the **API** level, where the store lookup actually runs |
| A text search for forbidden words flags the docstring that forbids them | walk the AST, or match multi-word phrases |
| macOS has no `timeout` | `curl --max-time` |
| A visually hidden (`sr-only`) form input is no longer where it looks, so clicks land on the label and pointer hit-testing misses it | style the real control in place with `appearance-none`; `bg-clip-content` plus padding draws a radio's dot |
| Conditionally rendering `DialogContent` alongside its own `open` state unmounts it before Radix's close cleanup runs | `lib/useLastPresent.ts` keeps the last value for the closing frame |
| Generated artifacts drift the moment regenerating becomes a step someone must remember | both exporters now have a script, and the demo samples have drift tests. Run them |

**Do not:** run `.claude/skills/bootstrap-project/scripts/init_boilerplate.sh` (targets an
unreachable internal host; its `unzip -o` would overwrite `apps/`). Do not blind-`cat >` a file
you have not read. Do not swap Postgres for Supabase (decided; `docs/canonical/03_architecture.md`
governs). Do not fill `sqlalchemy.url` in `alembic.ini` — `migrations/env.py` reads it from
`app.config` so the service and its migrations cannot diverge.

## 6. Next steps

1. **Fix the corpus/split artifact mismatch before anything else in sprint 05** — see § 7
   blocker 1. Sprint 05's task declares a dependency on the frozen grouped split, and that split
   currently cannot be joined to the published corpus at all. Small change, but everything
   downstream rests on it, and one decision inside it is the owner's.

2. **Sprint 05 — ranking models** (G6, 12 Sep), one task:
   [`sprint/backlog/05-ranking-models/backend/01-similarity-anomaly.md`](../sprint/backlog/05-ranking-models/backend/01-similarity-anomaly.md).
   Autonomous, and long. It creates `packages/model/` from scratch: six feature families, a
   TF-IDF character n-gram or MinHash similarity baseline, an Isolation Forest or LOF anomaly
   baseline, band calibration **on validation data only**, and a model card.

   Read `docs/canonical/05_model_card.md` § Feature families and § Risk aggregation first — the
   aggregation formula and all three caps are specified there verbatim, so they are not design
   decisions to make. The formula is
   `priority = max(deterministic_priority, calibrated_similarity, calibrated_anomaly)`, and the
   three caps already exist in the rules layer and must survive: no high band from text
   similarity alone; missing evidence plus an incomplete bundle lowers certainty toward *request
   evidence*; an exact duplicate fingerprint is high priority and still human-reviewed.
   **Store every component score and version, not just the aggregate.**

   Five tests carry the task and should be written first: group-split enforcement (training never
   sees test participants or provider-time blocks), serialization round-trip (a saved model
   reloads and reproduces identical predictions), feature-schema conformance, the **leakage
   probe** (no injector metadata reachable from features), and threshold boundaries.

   **Build so that removal is a clean revert.** Keep the model behind one call site and do not
   let its scores reach a wire model until sprint 06 has measured that they earn it.

3. **Sprint 06 — evaluation report** (G6). The last 501 endpoint, plus the `/evaluation` screen.
   The corpus, labels, frozen split and leakage report all live in `packages/data/build/`.

4. **Sprint 07 — demo hardening** (G8, 17 Sep). Owns the demo/reset route and the offline
   rehearsal; the ingest screen deliberately left that route to this sprint.

5. **Proposal work, unscheduled but real.** Four gaps against the competition guidance, none of
   them code: payer/customer identification; the business case framed as a cost model with stated
   assumptions (never a savings claim); field user validation; and impact on underserved regions.
   The affected file is `docs/canonical/09_proposal_evidence_map.md`.

**Owed cleanups**, none blocking: `app/service/evidence_graph.py` is 516 lines and
`app/service/case_query.py` is 469 (both above the 200–400 typical, both within the 800 maximum);
`docs/` is gitignored but `docs/HANDOVER.md`, `docs/api/`, `docs/canonical/` and
`docs/CONTINUE-PROMPT.md` are tracked from before that rule, so new files under `docs/` are
invisible to git.

**Two of these were cleared on 1 Sep.** The suite now runs against its own database
(`tilik_klaim_test`, created and migrated by `tests/conftest.py`), so `uv run pytest` no longer
wipes seeded dev data. And `ComparisonCandidate.candidate_case_id` is populated for
repeat-billing pairs via `BundleStore.case_id_for_bundle`, with the drawer rendering *Buka kasus
kandidat*. It stays `null` in two cases that are **correct, not defects**: a candidate accepted
but never screened has no case to open, and a cloned-documentation candidate is another
participant's note — cloning crosses that boundary and the service is handed the note, never the
submission behind it.

## 7. Blockers / decisions for the user

1. **`packages/data/build/` is internally inconsistent, and it blocks sprint 05.** Found while
   preparing this handover; nothing consumes those files yet, so it has been latent since
   sprint 01.

   `pipeline.write_artifacts()` writes `result.corpus.bundles` — the corpus **before**
   `strip_injector_traces()` runs. Two consequences:

   - **The published corpus still carries the injector tell.** 120 of 1,120 bundle ids look like
     `BND-00008-U798` and `BND-00016-R141`, announcing both that a record was injected and which
     injector did it. That is precisely what `strip_injector_traces` exists to remove. The
     leakage probe reported `leakage_passed: true` because it ran on `cleaned`, which never
     reached disk.
   - **`split.json` cannot be joined to `corpus.json`.** The split was computed on the renamed
     bundles, so its ids (`BND-0060398b8d24`) share **zero** overlap with the corpus ids
     (`BND-00000`) or with the label ids. `manifest.corpus_hash` likewise hashes a corpus that
     was never written.

   Reproduce both in one command:

   ```bash
   cd packages/data && python3 -c "
   import json
   corpus = {b['bundle_id'] for b in json.load(open('build/corpus.json'))}
   split  = json.load(open('build/split.json'))
   ids    = set(split['train']) | set(split['validation']) | set(split['test'])
   print('overlap:', len(corpus & ids))                     # prints 0
   print('leaky ids:', sum('-' in i[4:] for i in corpus))   # prints 120
   "
   ```

   **Status (1 Sep): the code and its tests are done; only the regeneration waits on you.**
   `BuildResult` now carries only the scrubbed bundles and the labels renamed to match, so
   reaching past the scrub is unrepresentable. `packages/data/tests/test_artifacts.py` asserts
   on the files themselves. The scrub also turned out to be incomplete — it rewrote `bundle_id`
   only, leaving `CLM-00008-U798` and `LN-00008-1-U798` inside the record, contradicting this
   task's own note that it "regenerates every identifier"; it now rewrites every marked
   identifier through one rename map.

   **The decision is smaller than it looked. `test_set_digest` does not change.** Measured
   against the real config: `ed903a4c39656e…` before and after, along with every partition
   count, the split membership, the multi-label ratio, and the leakage margin. The frozen test
   set is **not** re-frozen, so sprint 01's gate evidence survives intact. The only value that
   moves is `corpus_hash` (`db694e6851c9…` → `1ff95898c696…`), and it moves because the current
   one describes a corpus that was never written to disk. It is quoted in exactly one place,
   `packages/data/build/DATA_CARD.md`, which the pipeline regenerates.

   **What regenerating costs:** the four files under `packages/data/build/` are tracked in git,
   so it produces a large diff (`corpus.json` is 4.6 MB). **What it unblocks:** sprint 05 cannot
   fit a model on the published corpus until the artifacts join, and sprint 06 cannot score
   against it. To do it:

   ```bash
   (cd packages/data && uv run python -m tilik_data.pipeline --out build)
   ```

2. **`react-router-dom` v6 carries two moderate advisories** (open redirect via backslash in
   `<Link>`/`useNavigate`; constructor injection in SSR `deserializeErrors`). Both predate these
   sessions. The SSR one does not apply — this app is client-only. Fixing them means a breaking
   upgrade to v7, not taken mid-sprint without asking.

3. **The proposal must drop its Synthea claim.** ADR-0003 replaced Synthea with a native
   generator, so slide 8 can no longer cite Synthea's Apache-2.0 licence as evidence of a
   recognised privacy-safe source. The honest replacement is narrower and still true: the corpus
   is wholly synthetic, generated by project code, seeded and reproducible, and no real patient
   record of any origin was involved.

4. **`docs/Pedoman_Healthkathon_2026.docx` is unverified and probably not authentic.** Its
   metadata is machine-generated (creator "Un-named", empty `app.xml`, created and modified 13 ms
   apart), and the data portal it cites — `slicedata.bpjs-kesehatan.go.id` — **does not resolve**.
   The real portal is `data.bpjs-kesehatan.go.id`, whose Data Sampel needs a CAPTCHA-gated account
   and, judging by its description, lacks the RME resources this system screens. Treat every
   factual detail in that DOCX as unconfirmed until cross-checked against the official PDFs. Its
   judging criteria differ from the canonical six and should be handled as a **superset**, not a
   replacement.

5. **The design team still owes the annotation map for `/cases/:id`** — 27 widgets, the page most
   expensive to misread. The page is built and can be reviewed as it stands, so the map would
   confirm intent rather than unblock anything.

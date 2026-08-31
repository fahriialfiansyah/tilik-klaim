# HANDOVER — TilikKlaim

State snapshot for picking this up in a fresh session.
Pair with [`sprint/01-sprint-planning.md`](../sprint/01-sprint-planning.md), `changelog/{backend,web}.md`, and `docs/canonical/`.

- Repo: `/Users/fahrialfiansyah121gmail.com/Documents/HEALTHKATHON-2026/tilik-klaim`
- Branch: `development` · 16 commits, HEAD `a108950`, **working tree dirty — sprint 04 frontend
  task 02 is finished but uncommitted, awaiting the owner's review**. In sync with a PUBLIC
  GitHub remote (`github.com/fahriialfiansyah/tilik-klaim`) — do not push without asking
- Companion: [`CONTINUE-PROMPT.md`](./CONTINUE-PROMPT.md) boots a fresh session into the next
  task; [`qa/MANUAL-QA.md`](./qa/MANUAL-QA.md) is what the owner checks by eye
- Goal: a claim-evidence integrity layer that screens synthetic SATUSEHAT-shaped JKN claim
  bundles for four facility risk patterns and requires a logged human disposition. Healthkathon
  2026 entry, category *Efisiensi Risiko pada Fasilitas Kesehatan*; proposal due **19 September
  2026** (internal upload target 18 Sep)

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

- ingestion returns three states, and `VALID_WITH_NOTES` is *not* a softer `INVALID`;
- **a billed line with no supporting reference is a finding, not a completeness note.** An earlier
  version recorded it as incompleteness, which lowered certainty and would have defused the
  phantom detector entirely. `test_an_unevidenced_line_is_a_finding_not_a_completeness_note` locks
  this;
- an incomplete bundle *lowers* the band and routes to `REQUEST_EVIDENCE`, never toward
  `CONFIRM_ANOMALY`;
- case detail keeps `NOT_ASSESSABLE` distinct from `UNSUPPORTED`.

**Cloning is a per-provider pattern across different patients**, not per-patient. This cost a real
defect: `history_for()` scopes to same participant + provider (correct for repeat and unbundling),
which made clone detection silently inert through the API while service-level tests passed.
`peer_documents_for(provider_id)` now returns **only `DocumentRef`** — notes cross that wider
boundary, whole bundles never do.

**Three doc layers, one writer per fact.** `docs/canonical/` is read-only (change only via a new
ADR); `brief/` is the product blueprint in Indonesian; `sprint/` holds plans and task files in
English. Never restate a fact across layers.

**No LLM anywhere in the risk path, and no agents** (ADR-0002). The Workforce Manifest holds only
`be_service` and `fe_shell`.

## 2. Done so far

| Sprint | Gate | Status | Evidence |
|---|---|---|---|
| 00 — foundation | — | ✅ Done | both apps scaffolded and green |
| 01 — synthetic-data | G3 · 2 Sep | ✅ **Done, gate met early** | 1,120 bundles · 240 injections · leakage margin +0.0009 |
| 02 — ingest-validation | G4 · 5 Sep | ✅ Done | `POST /v1/bundles` + screen endpoint live on Postgres |
| 03 — evidence-rules | G4 · 5 Sep | ✅ **Done, gate met early** | 10 edge types, 4 risk modes, all caps enforced |
| 04 — review-slice | G5 · 9 Sep | ✅ **Done, gate met early** | `/`, `/cases/:id`, and `/ingest` all live on the real API; 14 Playwright specs green |
| 05 — ranking-models | G6 · 12 Sep | 📋 Planned | — |
| 06 — evaluation-report | G6 · 12 Sep | 📋 Planned | one endpoint still 501 |
| 07 — demo-hardening | G8 · 17 Sep | 📋 Planned | — |

**Verified this session** (re-run immediately before writing this):

```
backend 312 passed · domain 23 passed · data 47 passed · web 91 passed · tsc clean
playwright 14 passed in 9.6s · ruff: All checks passed
rsbuild 666.7 kB (390.0 kB gzip) · alembic head d1a7c3e50f42
```

The bundle grew from 551.4 kB because the case-detail feature and `@radix-ui/react-dialog`
landed. **Playwright is installed** — `@playwright/test` plus Chromium, config in
`apps/web/playwright.config.ts`, specs in `apps/web/tests/e2e/`, run with
`(cd apps/web && npm run test:e2e)`. It needs the API, the web dev server, and a **freshly
seeded** database; it reuses an already-running `npm run dev` rather than starting a second.

**Six of seven frozen endpoints are live.** Only `GET /v1/evaluations/{run_id}` still answers 501
naming sprint 06; `test_the_implemented_endpoints_no_longer_answer_501` guards against a
placeholder being left in front of working behaviour.

The full vertical slice runs end to end against real Postgres: ingest → screen → queue → detail →
disposition → audit, with all four risk modes firing and a stale write refused.

**Sprint 04 frontend, task 02 is done.** `/cases/:id` renders all 27 widgets against the live
seeded API: three columns, a source drawer, a comparison drawer, a confirmation dialog, and an
audit tab. All five binding display rules are implemented and each is asserted — reason before
score, counter-evidence outside the collapsible, a single-track evidence path, every reference
openable, and the whole flow keyboard-operable. Details in `changelog/{web,backend}.md`; the
click-through and 16 screenshots are in `docs/qa/MANUAL-QA.md` § 1b.

**The screen needed four additive API changes**, all defaulted fields that leave the frozen
contract and the committed fixtures intact. Each was a display rule that could not be met
correctly in the client, and three of them looked finished until the page was open:

| Change | What was wrong before |
|---|---|
| `counter_evidence_notes` | The rules wrote the sentence; the DTO shipped only the refs. Widget 13 was a bare resource id under a "counter-evidence" heading — a heading with no argument under it |
| `sources` (four availabilities) | Nothing resolved a reference to anything, so "every reference must open" had no mechanism. `MISSING` is *recorded* rather than omitted, because a dropped reference renders as a shorter list |
| real `ComparisonField`s | `fields` came from the reason's own component scores with left = right and `matches` hard-coded true — a comparison in which nothing could differ |
| `expected_support` on the catalog | `required_evidence` is what the *reason* needs to be well formed. Rendering it as "expected evidence" told the reviewer everything had been found, on a phantom case whose whole finding is an absence |

Reasons are now ordered strongest-first **in the response**, once, so the queue row, the case
header, and the reason cards cannot disagree about what to read first.

**Two more defects were only visible in a browser**, and one only with a keyboard:
`scripts/seed_dev.py` cleared bundles but not cases, leaving orphan cases pointing at deleted
ingestions so the detail endpoint answered `lines: []` on data that looked freshly seeded; and
closing any drawer dropped focus to `<body>`, because Radix restores focus to a `DialogTrigger`
this app does not use. Both are recorded in `docs/qa/MANUAL-QA.md` § 3.

**Sprint 04 frontend, task 03 is done — the sprint is closed.** `/ingest` renders widgets 1–11:
a drop zone whose limits are readable before an upload, the five curated scenarios, the
validation report, the error table, the copyable input hash, and exactly one button. The absence
of a configuration wizard is the feature, and it is enforced by the contract as well as the UI —
`ScreenRequest` carries no detector, threshold, or mode to offer.

**The five samples are generated, not copied.** `apps/backend/scripts/export_demo_samples.py`
writes them from the gold fixtures into `apps/web/public/samples/`; `tests/test_demo_samples.py`
fails if they drift, if a scenario loses the history its cross-claim rules need, or if a
fixture's **answer key** ever reaches the browser. Static files rather than a new endpoint,
because sprint 07 owns the demo/reset route and the demo has to run with no external network.

**One defect worth carrying forward: a refused bundle is not a broken service.** The API refuses
along two paths — a `4xx` envelope before parsing (oversized, malformed, too deep) and a `200`
report with `status: INVALID` after it. A plain `catch` renders the first as "the request
failed" and offers a retry on a file that will be refused identically every time, while hiding
the stable code the operator needs. `ApiError` now carries the server's `issues`, and
`features/review/ingest/rejection.ts` maps all three refusal sources onto one status.

**Design.** The team's mockup landed and was unpacked: `design/tokens.css` (35 colour tokens × 2
themes, plus type scale, spacing, radius, semantic band aliases), `design/mockup/reference.html`
(readable markup for all four screens — the bundle itself is one 405 kB base64 line), and
`design/mockup/unpack.py` so the next revision resyncs mechanically. Contrast measured: all five
status bands clear AA in both themes; `--t-3` was corrected to `#6b7977` (4.54:1).

**Toolchain installed 1 Sep** after an explicit go-ahead: **Tailwind v4 + shadcn/ui**. Tailwind v4
is CSS-first, so there is no `tailwind.config.ts` — the theme is a `@theme inline` block in
`apps/web/src/styles/app.css` pointing at `src/styles/tokens.css`, which is a literal `cp` of
`design/tokens.css`. **Tailwind's default colour palette is deleted** (`--color-*: initial`) so
`bg-red-500` no longer exists: red-only-for-conflict and green-only-for-completed-actions are now
enforced by the build instead of by review. Fonts are self-hosted (`@fontsource`, latin subsets
only) because the demo runs offline.

**Sprint 04 frontend, tasks 00 and 01 are done.** `/` (Antrean Review) renders from the live
seeded API: five operational metrics that each apply their own filter, server-side filters for
status/mode/band/date-range/search, four server-side sort keys, and a queue whose first column is
the working-language reason sentence. All four empty-and-error states are visually distinct and
were each confirmed in the browser, not only by test.

**Four defects were found by looking at the running page rather than by the compiler**, and all
four are the kind that pass review:

| Defect | Why it was invisible |
|---|---|
| Queue and case detail disagreed about evidence completeness on **every** case | `evidence_completeness()` fell back to the count of *unsupported* lines, so `supported_lines` was 0 by construction. The queue said "Tidak ada baris tertagih" about fully supported claims — a plausible-looking sentence that was simply false. Fixed by recording `billed_line_count` at screening (migration `d1a7c3e50f42`) |
| **Every** Button lost its text colour | `tailwind-merge` only knows Tailwind's stock type scale, so it read `text-body-lg` as a *colour*, judged it to conflict with `text-brand-on`, and kept the last. Primary buttons rendered near-black on dark teal at **2.5:1**. `cn()` now declares the project's scale |
| `--t-3` failed AA on two of three surfaces | August's correction measured it only against `--s-card`. The app also paints it on `--s-sunk` (4.33:1) and `--s-page` (4.07:1). Corrected to `#63706e` |
| `sort=age&order=desc` returned the **newest** case | Age displays as `now - screened_at`, which moves opposite to the timestamp being sorted — so "descending" meant "largest" on Amount and "smallest" on Age, from the same control |

The lesson generalises: **measure the rendered page, not the token file.** Contrast was
"verified" in August from token values alone and three of those checks were wrong.

**Manual QA lives in [`qa/MANUAL-QA.md`](./qa/MANUAL-QA.md)** — five queue states in
`qa/2026-09-01-antrean-review/`, sixteen case-detail states in `qa/2026-09-01-detail-kasus/`
(including the stale-version banner, the save failure, the not-found page, and the loading
skeleton), and nine ingest states in `qa/2026-09-01-ingest/` (all three validation outcomes,
both refusal paths, the identical-bundle notice, and the service failure). Every session that adds a screen appends a section there — the owner verifies wording
and colour meaning by eye, which no test does. `docs/` is gitignored, so these live locally
only.

## 3. Environment

- **Python**: `uv` manages 3.11. System Python is 3.9 and too old. Never activate a venv manually —
  `uv run` handles it.
- **Node**: 20.x for `apps/web`.
- **Postgres 16** via Docker Compose, container `tilik_klaim_db`, **host port 55432** on this
  machine (`DB_PORT` in the repo-root `.env`; the compose default is still 5432 for teammates).
- **Docker Desktop dies often here.** `open -a Docker`, then wait for `docker info` to answer.
- Secrets: `apps/backend/.env` (gitignored), template in `.env.example`. Local credentials are
  `tilik` / `tilik` / `tilik_klaim` — synthetic data only, nothing sensitive.
- **The backend runs with no database at all**, falling back to in-memory stores. That is a
  requirement, not a convenience: the demo runbook needs an offline run and the frontend team has
  no Docker. Without Postgres, 14 integration tests `skip` — they do not fail.

## 4. Build / run / test / verify

```bash
# --- database (optional; API runs without it) ---
open -a Docker && sleep 25                    # macOS; daemon is flaky here
docker compose up -d db                       # waits ~10s to report healthy
cd apps/backend && uv run alembic upgrade head
uv run python scripts/seed_dev.py             # 5 gold scenarios, ingested + screened

# --- the verify commands; run ALL after every change ---
(cd apps/backend   && uv run pytest)          # expect 285 passed (271 + 14 skipped without DB)
(cd packages/domain && uv run pytest)         # expect 21 passed
(cd packages/data  && uv run pytest)          # expect 47 passed
(cd apps/web       && npx tsc --noEmit)       # expect silence
(cd apps/web       && npm test)               # expect 18 passed (vitest)
(cd apps/backend   && uv run ruff check app tests)   # expect "All checks passed!"

# --- run the services ---
(cd apps/backend && uv run uvicorn app.main:app --reload --port 8000)
(cd apps/web     && npm run dev)              # :3000

# --- regenerate the synthetic corpus (deterministic) ---
(cd packages/data && uv run python -m tilik_data.pipeline --out build)

# --- DBeaver / any SQL client ---
# host localhost · port 55432 · db tilik_klaim · user tilik · password tilik
```

## 5. Conventions & gotchas

**Conventions.** Conventional Commits, one line, no watermark trailer. Code identifiers in
English, user-facing text in Indonesian. Backend code in `apps/backend/app/{router,service,dto,store}/`;
shared types in `packages/domain`; generator in `packages/data`; frontend domain components in
`apps/web/src/features/{domain}/{feature}/components/` — **never** bare `src/components/`;
navigation only in `src/config/menu/*`. Immutable models (`frozen=True`), files 200–400 lines,
functions under 50, explicit error handling, no magic numbers. When a task completes: tick every
`## TODOs` box, set the top-of-file `**Status:** ✅ Done` (the header is the source of truth), and
append to `changelog/{backend,web}.md`.

**Traps hit this session, with the fix:**

| Trap | Fix |
|---|---|
| `uv run pytest` **empties the dev database** — fixtures call `clear()` on the same `DATABASE_URL` | re-seed with `scripts/seed_dev.py`; a separate test database is still owed |
| Port 5432 gets stolen by **VS Code's automatic port forwarding** after a container stops; symptom is a healthy container but *password authentication failed for user "tilik"* | `lsof -nP -iTCP:5432 -sTCP:LISTEN` to find the owner; this machine uses `DB_PORT=55432` |
| `ruff` B008 on `Depends()` in argument defaults | use `Annotated[T, Depends(f)]`, the modern FastAPI form |
| `SourceType` has no `EMR`/`BILLING` — only `SYNTHETIC_GENERATOR`, `UPLOADED_BUNDLE`, `GOLD_FIXTURE` | correct as-is: provenance records how a record entered *this* system |
| `ClaimStatus` has no `SUBMITTED` (`DRAFT`/`ACTIVE`/`CANCELLED`/`ENTERED_IN_ERROR`) | use `ACTIVE` |
| Service-level tests passing `fixture.history` directly **hid a live defect** | test cross-claim behaviour at the **API** level, where the store lookup actually runs |
| A text search for forbidden words flags the docstring that forbids them | walk the AST, or match multi-word phrases |
| macOS has no `timeout` | `curl --max-time` |
| `scripts/seed_dev.py` cleared bundles but not cases, so orphan cases pointed at deleted ingestions and `GET /v1/cases/{id}` answered `lines: []` | fixed — it now clears every store; if a case detail ever looks empty again, check the case's `ingestion_id` still exists |
| A visually hidden (`sr-only`) form input is no longer where it looks, so clicks land on the label and pointer hit-testing misses it | style the real control in place with `appearance-none`; `bg-clip-content` plus padding draws a radio's dot |
| Radix `Dialog` restores focus to `DialogTrigger`, which this app never uses — so it `preventDefault()`s the browser restore and focus falls to `<body>` | `components/ui/dialog.tsx` captures the focused element during render and restores it in `onCloseAutoFocus` |
| Conditionally rendering `DialogContent` alongside its own `open` state unmounts it before Radix's close cleanup runs | `lib/useLastPresent.ts` keeps the last value for the closing frame |

**Do not:** run `.claude/skills/bootstrap-project/scripts/init_boilerplate.sh` (targets an
unreachable internal host; its `unzip -o` would overwrite `apps/`). Do not blind-`cat >` a file you
have not read. Do not swap Postgres for Supabase (decided; `docs/canonical/03_architecture.md`
governs). Do not fill `sqlalchemy.url` in `alembic.ini` — `migrations/env.py` reads it from
`app.config` so the service and its migrations cannot diverge.

## 6. Next steps

1. **Sprint 05 — ranking models is next** (G6, 12 Sep). Sprint 04 is closed: all three
   user-facing screens are live against the real API, and `/evaluation` is the only route still
   a placeholder — it belongs to sprint 06.

   Note sprint 05's kill criterion before starting: if the hybrid adds no measurable value over
   rules-only, ML is **removed**, and that is an anticipated outcome rather than a failure. See
   item 3 in blockers before acting on it.

   Everything the next screen needs already exists: `components/ui/dialog.tsx` (a Radix drawer
   and modal with focus return fixed), `ExpandableText`, `lib/useLastPresent.ts`,
   `withStop`/`formatIfTimestamp` in `features/review/shared/format.ts`, the
   `{api,store,use*}.ts` pattern for server state beside persisted client state, and the
   Playwright harness — a new spec drops into `apps/web/tests/e2e/`, and `tests/e2e/helpers.ts`
   looks cases up by risk mode rather than by a pinned identifier so a re-seed cannot break it.
2. **Sprint 05 — ranking models** (G6, 12 Sep). Note the kill criterion: if the hybrid adds no
   measurable value over rules-only, ML is *removed*, and that is an anticipated outcome rather
   than a failure. See item 3 in blockers before acting on it.
3. **Sprint 06 — evaluation report** (G6). The last 501 endpoint. The corpus, labels, frozen
   split, and leakage report already exist in `packages/data/build/`.
4. **Sprint 07 — demo hardening** (G8, 17 Sep).
5. **Proposal work, unscheduled but real.** Four gaps were identified against the competition
   guidance and none is code: payer/customer identification, business case framed as a cost model
   with stated assumptions (never a savings claim), field user validation, and impact on
   underserved regions. Details in the analysis recorded earlier this session; the affected file
   is `docs/canonical/09_proposal_evidence_map.md`.

**Owed cleanups**, none blocking: a separate test database so `pytest` stops wiping dev data;
`app/service/evidence_graph.py` is 516 lines and `app/service/case_query.py` is 469 (both above
the 200–400 typical, both within the 800 maximum); `billed_line_count` back-fills as 0 on cases
screened before migration `d1a7c3e50f42` — re-seeding or re-screening fixes them, and the seeded
demo data is regenerated anyway. The Playwright specs run with a single worker against the shared
dev database, which is correct today (a disposition bumps a case version, so parallel specs would
manufacture the very conflict one of them tests for) but is the same shared-database rough edge.

**`docs/api/openapi.json` had drifted for two sprints** and is now regenerated. It was written
once at the contract freeze and never again, so it still described `ReasonDto` without its
counter-evidence notes and `/v1/cases` with ingest-only error codes that endpoint never returns.
`apps/backend/scripts/export_openapi.py` regenerates it; run it after any router or DTO change.
The frozen contract itself is `tests/test_api_contract.py` plus the fixtures under
`tests/fixtures/api/`, both of which read the live app — that JSON is documentation, not the
source of truth, which is exactly why nothing caught it going stale.

**`docs/` is gitignored but `docs/HANDOVER.md`, `docs/CONTINUE-PROMPT.md`, `docs/canonical/`,
and `docs/api/` are tracked** (they predate the ignore rule added in `a108950`). New files under
`docs/` — the QA screenshots, for instance — are therefore invisible to git. That is consistent
with the QA folder being a local artefact for the owner, but it is worth a deliberate decision
rather than an accident.

**`ComparisonCandidate.candidate_case_id` is still always `null`.** Resolving a candidate claim
back to *its* case would let the comparison drawer link through to it, which the spec does not
require but a reviewer would reach for. It needs a bundle-id → ingestion lookup the store does
not currently offer.

## 7. Blockers / decisions for the user

1. ~~**Tailwind + shadcn install.**~~ **Resolved 1 Sep** — Tailwind v4 + shadcn/ui, installed.
2. ~~**The 9 px micro-label question.**~~ **Resolved 1 Sep** — raised to 11 px by owner decision,
   applied at source in `design/tokens.css`. All three `design/DESIGN.md` § Deviasi items are now
   closed. What the design team still owes is the **annotation map for `/cases/:id`** — 27
   widgets, the page most expensive to misread. The page is now built and can be reviewed as
   it stands, so the map would confirm intent rather than unblock anything.
3. **`react-router-dom` v6 carries two moderate advisories** (open redirect via backslash in
   `<Link>`/`useNavigate`; constructor injection in SSR `deserializeErrors`). Both predate this
   session. The SSR one does not apply — this app is client-only. Fixing them means a breaking
   upgrade to v7, which was not taken mid-sprint without asking.
3. **The proposal must drop its Synthea claim.** ADR-0003 replaced Synthea with a native
   generator, so slide 8 can no longer cite Synthea's Apache-2.0 licence as evidence of a
   recognised privacy-safe source. The honest replacement is narrower and still true: the corpus
   is wholly synthetic, generated by project code, seeded and reproducible, and no real patient
   record of any origin was involved.
4. **`docs/Pedoman_Healthkathon_2026.docx` is unverified and probably not authentic.** Its
   metadata is machine-generated (creator "Un-named", empty `app.xml`, created and modified 13 ms
   apart), and the data portal it cites — `slicedata.bpjs-kesehatan.go.id` — **does not resolve**.
   The real portal is `data.bpjs-kesehatan.go.id`, whose Data Sampel needs a CAPTCHA-gated account
   and, judging by its description (participant service-history summaries), lacks the RME
   resources this system screens. Treat every factual detail in that DOCX as unconfirmed until
   cross-checked against the official PDFs. Its judging criteria differ from the canonical six and
   should be handled as a **superset**, not a replacement.

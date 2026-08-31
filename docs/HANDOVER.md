# HANDOVER — TilikKlaim

State snapshot for picking this up in a fresh session.
Pair with [`sprint/01-sprint-planning.md`](../sprint/01-sprint-planning.md), `changelog/{backend,web}.md`, and `docs/canonical/`.

- Repo: `/Users/fahrialfiansyah121gmail.com/Documents/HEALTHKATHON-2026/tilik-klaim`
- Branch: `development` · 13 commits, HEAD `b0c2f2c`, **in sync with a PUBLIC GitHub remote**
  (`github.com/fahriialfiansyah/tilik-klaim`) — do not push without asking
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
| 04 — review-slice | G5 · 9 Sep | 🚧 backend ✅ / frontend 📋 | queue, detail, disposition, audit all live |
| 05 — ranking-models | G6 · 12 Sep | 📋 Planned | — |
| 06 — evaluation-report | G6 · 12 Sep | 📋 Planned | one endpoint still 501 |
| 07 — demo-hardening | G8 · 17 Sep | 📋 Planned | — |

**Verified this session** (re-run immediately before writing this):

```
backend 269 passed · domain 21 passed · data 47 passed · tsc clean · rsbuild 165.6 kB
ruff: All checks passed · alembic head c44b0f894fc2
```

**Six of seven frozen endpoints are live.** Only `GET /v1/evaluations/{run_id}` still answers 501
naming sprint 06; `test_the_implemented_endpoints_no_longer_answer_501` guards against a
placeholder being left in front of working behaviour.

The full vertical slice runs end to end against real Postgres: ingest → screen → queue → detail →
disposition → audit, with all four risk modes firing and a stale write refused.

**Design.** The team's mockup landed and was unpacked: `design/tokens.css` (35 colour tokens × 2
themes, plus type scale, spacing, radius, semantic band aliases), `design/mockup/reference.html`
(readable markup for all four screens — the bundle itself is one 405 kB base64 line), and
`design/mockup/unpack.py` so the next revision resyncs mechanically. Contrast measured: all five
status bands clear AA in both themes; `--t-3` was corrected to `#6b7977` (4.54:1).

**Not done, and deliberately so:** the Tailwind + shadcn install. The design blocker is cleared but
that task is marked non-autonomous and awaits an explicit go-ahead.

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

# --- the four verify commands; run ALL after every change ---
(cd apps/backend   && uv run pytest)          # expect 269 passed (255 + 14 skipped without DB)
(cd packages/domain && uv run pytest)         # expect 21 passed
(cd packages/data  && uv run pytest)          # expect 47 passed
(cd apps/web       && npx tsc --noEmit)       # expect silence
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

**Do not:** run `.claude/skills/bootstrap-project/scripts/init_boilerplate.sh` (targets an
unreachable internal host; its `unzip -o` would overwrite `apps/`). Do not blind-`cat >` a file you
have not read. Do not swap Postgres for Supabase (decided; `docs/canonical/03_architecture.md`
governs). Do not fill `sqlalchemy.url` in `alembic.ini` — `migrations/env.py` reads it from
`app.config` so the service and its migrations cannot diverge.

## 6. Next steps

1. **Sprint 04 frontend — the immediate next work**, in this order:
   `00-port-design-tokens` (needs the go-ahead below) → `01-antrean-review` → `02-detail-kasus`
   (27 widgets; give it a fresh session) → `03-ingest-page`. Gate G5 is 9 September. The API is
   complete and seeded, so every screen can be built against real responses.
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
`app/service/evidence_graph.py` is 516 lines (above the 200–400 typical, within the 800 maximum).

## 7. Blockers / decisions for the user

1. **Tailwind + shadcn install for `apps/web`.** The design blocker is cleared and
   `design/tokens.css` is ready, but `00-port-design-tokens` is marked non-autonomous and a prior
   instruction explicitly held the install. Sprint 04 frontend cannot start without this decision.
2. **Two design questions belong to the design team**, recorded in `design/DESIGN.md` § Deviasi.
   The 9 px micro-labels (35 occurrences) are worth raising to 10–11 px — not a standards
   violation, but tiring in an all-day tool, and changing it shifts layout. The 13 px body size and
   the `--t-3` contrast were already resolved (contract updated; contrast corrected).
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

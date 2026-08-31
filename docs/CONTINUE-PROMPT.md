# Continuation Prompt — paste into a fresh session

Copy everything in the block below as the first message to the new agent.

---

You are continuing **TilikKlaim** — a claim-evidence integrity layer that screens synthetic
SATUSEHAT-shaped JKN claim bundles for four facility risk patterns and requires a logged human
disposition. It is a Healthkathon 2026 entry, category *Efisiensi Risiko pada Fasilitas
Kesehatan*; the proposal is due **19 September 2026** (internal upload target 18 Sep).

WORK DIR: `/Users/fahrialfiansyah121gmail.com/Documents/HEALTHKATHON-2026/tilik-klaim`
(git branch `development`, 13 commits, HEAD `b0c2f2c`, clean tree, in sync with a **PUBLIC
GitHub remote** — do NOT push without asking).

FIRST, read these in order (do not skip):
1. `docs/HANDOVER.md` — full state, environment, verified commands, and every trap already hit
2. `sprint/01-sprint-planning.md` — eight sprints with gates, deadlines, and what is done
3. `docs/canonical/01_product_decision.md` — scope tiers, kill criteria, prohibited actions
4. `docs/canonical/05_model_card.md` § Risk aggregation — the three band caps
5. `design/DESIGN.md` + `sprint/00-app-spec.md` — the four screens and every widget
6. `brief/03_ANTREAN_REVIEW.md` and `brief/04_DETAIL_KASUS_DISPOSISI.md` — the two screens you are
   about to build, in working language

KEY FACTS:
- **Stack:** Python 3.11 + FastAPI + Pydantic v2 + SQLAlchemy Core (`apps/backend`), React 18 + TS
  + Rsbuild + Zustand (`apps/web`), Postgres 16 via Docker Compose, shared `packages/domain`,
  synthetic corpus generator in `packages/data`. `uv` manages Python; system Python is 3.9.
- **Verify after every change — all five:** `(cd apps/backend && uv run pytest)` → 269 ·
  `(cd packages/domain && uv run pytest)` → 21 · `(cd packages/data && uv run pytest)` → 47 ·
  `(cd apps/web && npx tsc --noEmit)` → silent · `(cd apps/backend && uv run ruff check app tests)`.
- **Database is optional and the fallback is deliberate.** No Postgres → in-memory stores, 14
  tests skip rather than fail. The demo runbook requires an offline run and the frontend team has
  no Docker. To start it: `open -a Docker`, `docker compose up -d db`, `uv run alembic upgrade
  head`, then `uv run python scripts/seed_dev.py`. **Host port is 55432 here** (`DB_PORT` in the
  repo-root `.env`) because VS Code's port forwarding repeatedly steals 5432.
- **Done:** Sprints 00–03 complete, gates G3 and G4 both met early. Sprint 04 backend complete.
  Six of the seven frozen endpoints are live; only `GET /v1/evaluations/{run_id}` still answers
  501 (sprint 06). The full slice runs end to end: ingest → screen → queue → detail → disposition
  → audit, all four risk modes firing.
- **Design has landed.** `design/tokens.css` holds 35 colour tokens across light and dark plus
  type scale, spacing, radius, and semantic band aliases; `design/mockup/reference.html` is the
  readable markup for all four screens (the bundle is one 405 kB base64 line — read the reference,
  not the bundle). All five status bands clear AA contrast in both themes.
- **The ethical core is encoded in types and asserted by tests.** The system reports "risiko atau
  anomali yang perlu ditinjau" — never fraud, never claim rejection, never payment, sanction, code
  change, or medical necessity. **An incomplete record is not evidence a service was not
  delivered:** it resolves to *valid-with-notes*, lowers the band, and routes to "minta bukti",
  never toward "konfirmasi anomali". A billed line with no supporting reference is the opposite —
  a **finding**, not an incompleteness note; recording it as incompleteness once defused the
  phantom detector entirely. Case detail keeps `NOT_ASSESSABLE` distinct from `UNSUPPORTED`.
- **No LLM in the risk path, no agents** (ADR-0002). `docs/canonical/` is read-only; change it only
  via a new ADR.

RULES: Conventional Commits, one line, no watermark trailer; never push without asking. Code
identifiers in English, user-facing text in Indonesian. Frontend domain components go in
`apps/web/src/features/{domain}/{feature}/components/` — **never** bare `src/components/`; navigation
lives only in `src/config/menu/*`; bounded scroll regions use `PerfectScrollArea`. Immutable models
(`frozen=True`), files 200–400 lines, functions under 50, no magic numbers. When a task completes,
tick every `## TODOs` box, set the top-of-file `**Status:** ✅ Done` (the header is the source of
truth), and append to `changelog/{backend,web}.md`. **Read any file before overwriting it.** Never
run `.claude/skills/bootstrap-project/scripts/init_boilerplate.sh` (unreachable internal host; its
`unzip -o` would overwrite `apps/`). Do not fill `sqlalchemy.url` in `alembic.ini` — `migrations/env.py`
reads it from `app.config` so the service and its migrations cannot diverge. Be aware that
`uv run pytest` **empties the dev database**; re-seed with `scripts/seed_dev.py`. Red is reserved for
deterministic conflict and green only for completed, validated actions — green never marks a claim
safe, and a case with no signal reads "tidak ada risiko teramati", never "bersih" or "aman".

NEXT TASK: **Sprint 04 frontend**, gate G5 on 9 September. Start by asking the user to confirm the
Tailwind + shadcn install for `apps/web` — `sprint/backlog/04-review-slice/frontend/00-port-design-tokens.md`
is marked non-autonomous and a prior instruction explicitly held that install, so it needs an
explicit go-ahead before anything else can be styled. Then, in order: `00-port-design-tokens` →
`01-antrean-review` → `02-detail-kasus` (27 widgets — worth its own session) → `03-ingest-page`.
The API is complete and seeded, so build every screen against real responses rather than fixtures:
`GET /v1/cases` for the queue, `GET /v1/cases/{id}` for the detail,
`POST /v1/cases/{id}/dispositions` and `GET /v1/cases/{id}/audit` for the action panel and history.
The queue deliberately carries **no narrative text** — do not try to render a note preview there.
Afterwards: sprint 05 (ranking models), 06 (evaluation report — the last 501), 07 (demo hardening).

Verify each visible change by running the five verify commands above and reporting the pass counts,
and by loading the affected screen at http://localhost:3000 against a seeded database. Confirm
you've read the docs above, then proceed.

---

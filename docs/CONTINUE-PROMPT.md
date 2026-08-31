# Continuation Prompt — paste into a fresh session

Copy everything in the block below as the first message to the new agent.
Written for a **long unattended run**: every decision that would otherwise block is pre-answered.

---

You are continuing **TilikKlaim** — a claim-evidence integrity layer that screens synthetic
SATUSEHAT-shaped JKN claim bundles for four facility risk patterns and requires a logged human
disposition. Healthkathon 2026 entry, category *Efisiensi Risiko pada Fasilitas Kesehatan*;
proposal due **19 September 2026** (internal upload target 18 Sep).

WORK DIR: `/Users/fahrialfiansyah121gmail.com/Documents/HEALTHKATHON-2026/tilik-klaim`
(git branch `development`, 15 commits, HEAD `7d0fc47`, clean tree, **in sync with a PUBLIC
GitHub remote**. Do NOT push. Do NOT commit — the owner reviews the working tree first.)

FIRST, read these in order (do not skip):
1. `docs/HANDOVER.md` — full state, environment, verified commands, every trap already hit
2. `sprint/backlog/04-review-slice/frontend/02-detail-kasus.md` — your immediate task, 27 widgets
3. `sprint/00-app-spec.md` § 4 — the 27 widgets and the five binding display rules
4. `brief/04_DETAIL_KASUS_DISPOSISI.md` — the screen in working language, § 2 and § 4
5. `design/mockup/reference.html` — read the `data-screen-label="Detail Kasus"` section
   (line ~262). Read this file, **never** `tilik-klaim-v2.bundle.html` — that one is a single
   405 kB base64 line.
6. `docs/qa/MANUAL-QA.md` — what the owner checks by eye; you must extend it
7. `docs/canonical/01_product_decision.md` — scope tiers and prohibited actions

KEY FACTS:
- **Stack:** Python 3.11 + FastAPI + Pydantic v2 + SQLAlchemy Core (`apps/backend`), React 18 +
  TS + Rsbuild + **Tailwind v4 + shadcn/ui** + Zustand (`apps/web`), Postgres 16 via Docker,
  shared `packages/domain`, generator in `packages/data`. `uv` manages Python; system Python 3.9.
- **Run everything:** `./scripts/dev.sh --db` (API + Web + Postgres + migrations, Ctrl-C stops
  all). Then seed once: `(cd apps/backend && uv run python scripts/seed_dev.py)`. Web on :3000
  proxies `/v1` to the API on :8000, so the browser stays same-origin and the backend needs no CORS.
- **Verify after every change — all six:** `(cd apps/backend && uv run pytest)` → 285 ·
  `(cd packages/domain && uv run pytest)` → 21 · `(cd packages/data && uv run pytest)` → 47 ·
  `(cd apps/web && npx tsc --noEmit)` → silent · `(cd apps/web && npm test)` → 18 ·
  `(cd apps/backend && uv run ruff check app tests)`. Report the counts.
- **Tailwind v4 is CSS-first — there is no `tailwind.config.ts`.** The theme is an
  `@theme inline` block in `apps/web/src/styles/app.css` pointing at `src/styles/tokens.css`,
  which is a literal `cp` of `design/tokens.css`. **Tailwind's default colour palette is
  deleted** (`--color-*: initial`), so `bg-red-500` produces nothing on purpose. Use the
  semantic names: `bg-card`, `text-ink`, `border-line`, `bg-brand`, `text-band-conflict`,
  `bg-band-signal-bg`, `text-done`, `bg-notice-bg`. If you add a font size to `app.css`, add it
  to `FONT_SIZES` in `src/lib/utils.ts` too, or `tailwind-merge` will silently eat text colours.
- **Reuse what exists** rather than rebuilding: `src/lib/http.ts` (`request`, `query`,
  `ApiError`, `NetworkError`), `src/features/review/shared/{types,labels,format}.ts`,
  `BandBadge`, `EvidenceMeter`, `PerfectScrollArea`, `components/ui/button.tsx`, and the Vitest
  setup (`src/test/render.tsx`).
- **Done:** sprints 00–03; sprint 04 backend; sprint 04 frontend tasks `00-port-design-tokens`
  and `01-antrean-review`. Six of seven endpoints live; only `GET /v1/evaluations/{run_id}`
  answers 501 (sprint 06).

RULES: Conventional Commits when you eventually do commit — but **this run commits nothing and
pushes nothing**. Code identifiers in English, user-facing text in Indonesian. Frontend domain
components go in `apps/web/src/features/{domain}/{feature}/components/` — **never** bare
`src/components/`; navigation only in `src/config/menu/*`; bounded scroll regions use
`PerfectScrollArea`. Immutable models (`frozen=True`), files 200–400 lines, functions under 50,
no magic numbers. TDD: write the failing test first, then the implementation. When a task
completes, tick every `## TODOs` box, set the top-of-file `**Status:** ✅ Done` (the header is
the source of truth), and append to `changelog/{backend,web}.md`. **Read any file before
overwriting it.** Never run `.claude/skills/bootstrap-project/scripts/init_boilerplate.sh`.
Do not fill `sqlalchemy.url` in `alembic.ini`. `uv run pytest` **empties the dev database** —
re-seed with `scripts/seed_dev.py` afterwards. Red is only for deterministic conflict; green
only for completed, validated actions — green never marks a claim safe, and a case with no
signal reads "tidak ada risiko teramati", never "bersih" or "aman".

**Pre-authorised, so you do not stop to ask:**
- **Install Playwright** (`@playwright/test` + Chromium) — the owner approved this. Tasks 02, 03
  and sprint 07 all specify Playwright E2E tests. Put specs in `apps/web/tests/e2e/`.
- Adding **backward-compatible query parameters** to existing endpoints when a spec'd UI
  requirement cannot be met correctly client-side. Precedent: `mode`, `sort`/`order` and
  `search` were added to `GET /v1/cases` for exactly this reason — the response is paginated,
  so filtering or sorting in the client acts on one page and silently ignores the rest. Cover
  each with tests; never change a wire model (the contract is frozen).
- Adding npm packages that are **additive** (a date util, a diff renderer). Anything that
  replaces a core layer — a different state manager, router, or build tool — is a stack change
  and requires the owner.

NEXT TASK: **`sprint/backlog/04-review-slice/frontend/02-detail-kasus.md`** — gate G5 on
9 September. This is the densest page in the app: 27 widgets in three columns, plus a
comparison drawer and an audit tab. The density is deliberate; splitting it across screens
breaks the "one screen to resolve one reason" contract. Build against the **live seeded API**
as the queue does — `GET /v1/cases/{id}`, `POST /v1/cases/{id}/dispositions`,
`GET /v1/cases/{id}/audit` all work. Five display rules are binding: reason before score;
counter-evidence never hidden behind a collapsed panel; the evidence path stays a single track,
not a web; every evidence reference must actually open; the whole flow must be keyboard-operable.
Optimistic locking on `expected_case_version` is an accountability guarantee, not a nicety —
a rejected save must preserve the reviewer's input.

Then `03-ingest-page.md`. Afterwards, in order: sprint 05 (ranking models — note the kill
criterion: if the hybrid adds no measurable value over rules-only, ML is **removed**, and that
is an anticipated outcome, not a failure), sprint 06 (evaluation report — the last 501),
sprint 07 (demo hardening).

**Leave the working tree uncommitted** and, for each screen you finish, append a section to
`docs/qa/MANUAL-QA.md` with a numbered click-through and save screenshots of every state
(loading, empty, error, populated, and for `/cases/:id` also the stale-version state) into
`docs/qa/<date>-<screen>/`. The owner verifies these by eye in the morning; that is the whole
point of the folder.

Verify each visible change by running the six verify commands above and reporting the pass
counts, and by loading the affected screen at http://localhost:3000 against a seeded database.
Confirm you've read the docs above, then proceed.

---

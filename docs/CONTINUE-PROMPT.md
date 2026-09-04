# Continuation Prompt — paste into a fresh session

Copy everything in the block below as the first message to the new agent.

---

You are continuing **TilikKlaim** — a claim-evidence integrity layer that screens synthetic
SATUSEHAT-shaped JKN claim bundles for four facility risk patterns and requires a logged human
disposition. Healthkathon 2026 entry, category *Efisiensi Risiko pada Fasilitas Kesehatan*.

**Today is 4 September 2026. Registration closes 14 September; the proposal closes 19 September,
internal upload target 18 September.**

WORK DIR: `/Users/fahrialfiansyah121gmail.com/Documents/HEALTHKATHON-2026/tilik-klaim`
(git branch `development`, 40 commits, HEAD `1bee0fb`, in sync with a PUBLIC GitHub remote.
**Do NOT push.** Commit your own work in small Conventional Commits as you finish each piece —
the owner reviews the log in the morning. Leave `scripts/dev.sh` alone; that modification is
theirs, in progress.)

**READ THIS FIRST, AND BELIEVE IT: every sprint's code is finished.** Ten sprints, eight `✅`.
Sprints 06 and 07 are `🚧` and **neither is waiting on an engineer** — they are waiting on
signatures, a rehearsal, and a recording. If you go looking for a feature to build, you will
build something nobody asked for. Read `docs/HANDOVER.md` § 6 before you touch anything.

FIRST, read these in order (do not skip):
1. `docs/HANDOVER.md` — full state, environment, verified commands, every trap already hit,
   § 6 what is actually left, § 7 the open decisions
2. `sprint/01-sprint-planning.md` — the sprint table and the deadline clock
3. `docs/canonical/01_product_decision.md` — the ethical core and the kill criteria
4. `docs/qa/MANUAL-QA.md` — what the owner checks by eye, if any screen changes

KEY FACTS:
- **Stack:** Python 3.11 + FastAPI + Pydantic v2 + SQLAlchemy Core (`apps/backend`), React 18 +
  TS + Rsbuild + Tailwind v4 + shadcn/ui + Zustand (`apps/web`), Postgres 16 via Docker, shared
  `packages/domain`, generator in `packages/data`, models in `packages/model`, offline metrics in
  `evaluation/`. `uv` manages Python; system Python is 3.9 and too old.
- **Verify after every change — all eight, and report the counts:**
  `(cd apps/backend && uv run pytest)` → 467 · `(cd packages/domain && uv run pytest)` → 23 ·
  `(cd packages/data && uv run pytest)` → 57 · `(cd packages/model && uv run pytest)` → 71 ·
  `(cd evaluation && uv run pytest)` → 47 · `(cd apps/web && npx tsc --noEmit)` → silent ·
  `(cd apps/web && npm test)` → 184 · `(cd apps/backend && uv run ruff check app tests)`.
  End-to-end: `(cd apps/web && npm run test:e2e)` → 24.
- **`uv sync` in `apps/backend` silently uninstalls `tilik-domain`.** The next test run fails with
  `ModuleNotFoundError` that reads like broken code. Fix:
  `(cd apps/backend && uv pip install -e ".[dev]" -e ../../packages/domain)`.
- **The test suite must never touch the network.** `tests/conftest.py` pins `BRIEFING_ENABLED`
  off and redirects the database, for the same reason: a run must not depend on the developer's
  `.env`. If a suite suddenly takes minutes, that pinning has regressed.
- **`docs/` is gitignored.** New files under it need `git add -f` or they are invisible.
- **The ethical core is in the types and asserted by tests, not a style preference.** The system
  reports "risiko atau anomali yang perlu ditinjau" — never fraud, never a rejection, never a
  payment action, never a sanction. Red is only for deterministic conflict; green only for a
  completed, validated action, and green never marks a claim safe. A case with no signal reads
  "tidak ada risiko teramati", never "bersih" or "aman".
- **No LLM in the risk score** (ADR-0002). The one LLM in the repo is the bounded, read-only
  Case Briefing (ADR-0005) — off by default, outside the risk path, and
  `tests/test_briefing_isolation.py` asserts in both directions that it stays there. **If that
  test ever fails, revert the feature; do not fix it in place.**

WHAT IS ACTUALLY LEFT — none of it is a coding task:

**(a) Sprint 06 — three sign-offs, then flip the table.** Both tasks are `✅`; the official run
`run-20260901T110000Z` is in `evaluation/artifacts/`. Open: experiment record (M1), claim
interpretation (M3), visuals (M2), plus M1's validation of `docs/artifacts/failure-modes.md`.
Separate signatures are deliberate — whoever produced a number should not be the only one
deciding what it may claim. **Flipping sprint 06 to `✅` is the owner's signature, not yours.**
It also closes ADR-0005's stated precondition, which the briefing shipped ahead of.

**(b) Sprint 07 — a rehearsal and a recording.** Everything machine-checkable is done. Still
owed, by a person: the three-minute flow rehearsed with narration on the presentation machine
offline, and the **1080p fallback recorded with the application stopped**. § 22 says the fallback
is played, not troubleshooted — it must exist before the day, and it is the most
schedule-exposed item remaining.

**(c) Proposal work — the largest remaining effort.** Four gaps in
`docs/canonical/09_proposal_evidence_map.md`: payer/customer identification; the business case as
a **cost model with stated assumptions, never a savings claim**; field user validation; impact on
underserved regions. Separately, slide 8 must drop its Synthea claim — ADR-0003 replaced Synthea
with a native generator (`docs/HANDOVER.md` § 7 item 2 has the honest replacement wording).

**If the owner asks for engineering anyway**, these are the real candidates, in order:
- `apps/backend/.env` currently has `BRIEFING_ENABLED=true`, left on after gateway testing on
  4 Sep. **Set it to `false` before any offline demo rehearsal** — § 22 forbids depending on a
  remote LLM, and the deterministic template is the demo path.
- `case-detail-a11y.spec.ts` asserts `toHaveCount(0)` on broken evidence references before the
  detail finishes loading, so it cannot catch the class of defect found on 3 Sep. Add a
  `waitFor` on the matrix first.
- `evidence_graph.py` (543 lines) and `case_query.py` (473) are above the 200–400 typical,
  within the 800 maximum.
- The briefing's LLM path answers 9 of 15 runs; the rest fall back to the template and say why.
  `BRIEFING_MAX_OUTPUT_TOKENS` trades latency against truncation. The real fix is a gateway that
  emits EOS after guided JSON — see `docs/HANDOVER.md` § 7 item 6.

RULES: Code identifiers in English, user-facing text in Indonesian. Immutable models
(`frozen=True`), files 200–400 lines, functions under 50, no magic numbers, explicit error
handling. **TDD: write the failing test first, then the implementation.** When a task completes,
tick every `## TODOs` box, set the top-of-file `**Status:** ✅ Done` (the header is the source of
truth), append to `changelog/{backend,web}.md`, and update `sprint/01-sprint-planning.md`.
Completed sprints stay in `sprint/backlog/` — do not create `active/` or `archive/` folders.
**Read any file before overwriting it.** Never run
`.claude/skills/bootstrap-project/scripts/init_boilerplate.sh`. Do not fill `sqlalchemy.url` in
`alembic.ini`. Regenerate `docs/api/openapi.json` with
`(cd apps/backend && uv run python scripts/export_openapi.py)` if you touch a router or DTO.

**Not pre-authorised:** pushing to the remote; flipping sprint 06 to `✅`; enabling the briefing
in any committed file; writing the vLLM gateway address or API key into anything git tracks —
`.env.example` documents the names and leaves both empty, and a test asserts it.

Verify each change by running the eight commands above and reporting the pass counts; for
anything that changes a screen, also load it at <http://localhost:3000> against a seeded
database, save screenshots of every state into `docs/qa/<date>-<screen>/`, and append a numbered
click-through to `docs/qa/MANUAL-QA.md`. Confirm you've read the docs above, then proceed.

---

# Continuation Prompt — paste into a fresh session

Copy everything in the block below as the first message to the new agent.

---

You are continuing **TilikKlaim** — a claim-evidence integrity layer that screens synthetic
SATUSEHAT-shaped JKN claim bundles for four facility risk patterns and requires a logged human
disposition. It is a Healthkathon 2026 entry; the proposal is due **19 September 2026**
(internal upload target 18 Sep). Today's engineering gate is **G4 on 5 September**.

WORK DIR: `/Users/fahrialfiansyah121gmail.com/Documents/HEALTHKATHON-2026/tilik-klaim`
(git branch `development`, 5 commits, HEAD `5a5aa78`, clean tree, **pushed to a PUBLIC GitHub
remote** — do NOT push or force-push without asking).

FIRST, read these in order (do not skip):
1. `docs/HANDOVER.md` — full state, environment, verified commands, traps already hit
2. `sprint/01-sprint-planning.md` — 8 sprints with gates, deadlines, owners, and what is done
3. `brief/00_OVERVIEW.md` — product blueprint, 6 modules, and the Workforce Manifest
4. `docs/canonical/01_product_decision.md` — scope tiers and the kill criteria
5. `docs/canonical/03_architecture.md` — components, the 9 evidence edges, the 7 API contracts
6. `sprint/00-app-spec.md` — the 4 pages and every widget, mapped back to brief modules

KEY FACTS:
- **Stack:** Python 3.11 + FastAPI + Pydantic v2 (`apps/backend`), React 18 + TS + Rsbuild +
  Zustand (`apps/web`), plain Postgres via Docker Compose, shared `packages/domain`.
  `uv` manages Python; system Python is 3.9 and too old.
- **Verify before and after every change:** `(cd apps/backend && uv run pytest)` → 64 passed ·
  `(cd packages/domain && uv run pytest)` → 21 passed · `(cd apps/web && npx tsc --noEmit)` →
  silent · `(cd apps/web && npx rsbuild build)` → ~165 kB.
- **Done:** Sprint 00 (scaffold, both apps green). Sprint 01's foundation
  `00-canonical-schema` — 11 schema domains, 7 reason codes across 4 risk modes, 10 evidence
  edge types, 5 gold fixtures. Sprint 02's foundation `00-api-contract` — 7 endpoints in
  `docs/api/openapi.json`, 18 stable error codes, 10 committed example responses.
- **Three doc layers, one writer per fact:** `docs/canonical/` is **read-only** (change only via
  a new ADR); `brief/` is the product blueprint in Indonesian; `sprint/` holds the plan and task
  files in English. Never restate a fact across layers.
- **Ethical core, encoded in types and asserted by tests:** the system reports "risk or anomaly
  requiring review" — never fraud, never claim rejection, never payment or sanction, never
  medical necessity. An **incomplete record is not evidence a service was not delivered**:
  that resolves to *valid-with-notes* and routes to "request evidence", never to "confirm
  anomaly". **No LLM in the risk path, no agents** (ADR-0002; the Workforce Manifest holds only
  `be_service` and `fe_shell`).
- **Frontend is unblocked and can run in parallel** against
  `apps/backend/tests/fixtures/api/*.json` — no running backend needed.
- **Where things go:** backend code `apps/backend/app/{router,service,dto,store}/`; shared types
  `packages/domain/src/tilik_domain/`; generator `packages/data/`; models `packages/model/`;
  frontend domain components `apps/web/src/features/{domain}/{feature}/components/` (never bare
  `src/components/`); navigation only in `src/config/menu/*`.

RULES: Conventional Commits, never push without asking. Code identifiers in English,
user-facing text in Indonesian (`apps/web/src/pages/queue/QueuePage.tsx` renders `Antrean Review`); screen
ids in `design/flow.json` must match `APP_MENU` ids exactly. Immutable models (`frozen=True`),
files 200–400 lines, functions under 50, explicit error handling, no magic numbers. When a task
completes: tick every `## TODOs` box, set the top-of-file `**Status:** ✅ Done`, and append to
`changelog/{web,backend}.md` — the header is the source of truth. **Read any file before
overwriting it** (a blind `cat >` on `.gitignore` earlier nearly committed the gitignored
`.claude/` office skills into this public repo). **Never run**
`.claude/skills/bootstrap-project/scripts/init_boilerplate.sh` — it targets an unreachable
internal office host and `unzip -o` would overwrite `apps/`. Do not install Tailwind or shadcn
yet (waiting on `design/tokens.css` from the design team), and do not swap Postgres for Supabase
(decided; `docs/canonical/03_architecture.md` governs). Assert Pydantic `model_fields` from the
class, not an instance. On macOS there is no `timeout` — use `curl --max-time`.

NEXT TASK: Implement `sprint/backlog/03-evidence-rules/backend/01-evidence-graph.md`, then
`sprint/backlog/03-evidence-rules/backend/02-rule-engine.md`. This closes **Gate G4 (5 Sep)** and needs no Synthea — the five gold
fixtures in `apps/backend/tests/fixtures/gold/` are hand-built. Derive the canonical evidence
edges over a validated bundle, then emit versioned reason codes with resolvable evidence **and
counter-evidence** for phantom, repeat, and unbundling. Success looks like: the phantom fixture
screens to `LINE_WITHOUT_COMPLETED_PROCEDURE` with every evidence reference resolving, the clean
fixture produces no reason at all, and screening the same input hash at the same engine version
is deterministic. Respect the band caps — text similarity alone can never reach the top band,
and a missing-evidence-plus-incomplete-bundle combination *lowers* certainty rather than raising
a signal. Afterwards, in order: `sprint/backlog/02-ingest-validation/backend/01-bundle-ingestion.md`, then
`sprint/backlog/04-review-slice/frontend/` (which can also start immediately in parallel).

Verify each change by running the four verify commands above and reporting the pass counts.
Confirm you've read the docs above, then proceed.

---

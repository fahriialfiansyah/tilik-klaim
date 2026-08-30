# HANDOVER — TilikKlaim

State snapshot for picking this up in a fresh session.
Pair with [`brief/00_OVERVIEW.md`](../brief/00_OVERVIEW.md), [`sprint/01-sprint-planning.md`](../sprint/01-sprint-planning.md), and [`docs/canonical/`](canonical/).

- Repo: `/Users/fahrialfiansyah121gmail.com/Documents/HEALTHKATHON-2026/tilik-klaim`
- Branch: `development` · **pushed to a PUBLIC GitHub remote** (`fahriialfiansyah/tilik-klaim`) · 5 commits · HEAD `5a5aa78` · working tree clean
- Goal (one line): A claim-evidence integrity layer that screens synthetic SATUSEHAT-shaped JKN claim bundles for four facility risk patterns and requires a logged human disposition — built for Healthkathon 2026, proposal due **19 September 2026**.

---

## 1. Orientation (read first)

**This is a competition entry, not a product build.** Two clocks run at once: an engineering
clock (gates G3–G8) and a proposal clock (submission 19 Sep, internal target 18 Sep). Work
that does not produce evidence for the proposal is usually the wrong work.

**Three document layers, one writer per fact.** Do not restate across layers — the master
plan's § 19 anti-duplication rule is enforced here:

| Layer | Path | Contains | Editable? |
|-------|------|----------|-----------|
| Canonical | `docs/canonical/` | Rules, product decision, architecture, data card, model card, evaluation plan, threat model | **Read-only.** Change only via a new ADR in `docs/canonical/decisions/` |
| Brief | `brief/` | Product blueprint, 6 modules, business-technical language, Indonesian | Yes |
| Sprint | `sprint/` | Page spec, sprint plan, per-stack task files, English | Yes |

The `.docx` at `docs/HEALTHKATHON_2026_WINNING_MASTER_PLAN.docx` is the origin of all three.
It is an archive — read it for context, never edit it.

**Two vocabularies that are easy to conflate:**

- *Stage* (`brief/00_OVERVIEW.md`) is `MVP` — this governs the pipeline rules and permits real
  backend work. *Maturity label* to judges is `functional prototype` — a competition claim.
  They are different axes. Do not "fix" one to match the other.
- *Injection ground-truth label* ≠ *fraud label*. The generator injects known patterns so
  detection can be scored. It says nothing about anyone's conduct.

**The ethical constraint is load-bearing, not decoration.** The system reports "risk or
anomaly requiring review". It never states fraud, rejects a claim, stops payment, imposes a
sanction, alters a code, or decides medical necessity. Most subtly: **an incomplete record
looks identical to a billed-but-unevidenced service**, and conflating them is how this system
would produce false accusations. That distinction is encoded in types
(`ValidationStatus.VALID_WITH_NOTES`, `support_state="NOT_ASSESSABLE"`) and asserted by tests.

**No LLM anywhere in the risk decision path.** Locked by
`docs/canonical/decisions/ADR-0002-no-llm-in-risk-score.md`. No agents either — the brief's
Workforce Manifest holds only `be_service` and `fe_shell`, deliberately, so `sprint-builder`
never injects an agent-management sprint.

## 2. Done so far

**Sprint 00 — Foundation ✅ Done (verified)**

| Item | Evidence |
|------|----------|
| FastAPI service, env-driven config, `/healthz` reporting engine identity + `data_class: synthetic` | `uv run pytest` green |
| React 18 + TS + Rsbuild shell, config-driven menu, 4 routes | `tsc --noEmit` clean; build 165.6 kB (55.0 kB gzip) |
| Local Postgres via Docker Compose, no external network | `docker compose config -q` valid |

**Sprint 01 — Synthetic Data 🚧 In Progress · Gate G3 due 2 Sep 18:00**

- ✅ `sprint/backlog/01-synthetic-data/backend/00-canonical-schema.md` (**foundation — unblocks Sprints 02/03/04/06**).
  `packages/domain` installable: 11 schema domains, 7-entry reason catalog covering all 4 risk
  modes, 10 evidence edge types, 5 committed gold fixtures. **62 tests passing.**
- 📋 `01-synthea-adapter`, `02-risk-injectors`, `03-split-and-leakage-controls` (all under
  `sprint/backlog/01-synthetic-data/backend/`) — **blocked on
  Java + Synthea** (see § 7).

**Sprint 02 — Ingest & Validation 🚧 In Progress · Gate G4 due 5 Sep**

- ✅ `sprint/backlog/02-ingest-validation/backend/00-api-contract.md` (**foundation — unblocks Sprint 04 frontend**).
  7 endpoints in `docs/api/openapi.json`, 29 wire models, 18 stable error codes, 10 committed
  example responses. **64 tests passing.**
- 📋 `sprint/backlog/02-ingest-validation/backend/01-bundle-ingestion.md`.

**Sprints 03–07 — 📋 Planned.** 21 task files total, each carrying its WS spec's Acceptance as
`## Done when` and its Tests + Edge cases as TODO checkboxes.

**Not started and correctly so:** `design/tokens.css` and HTML mockups — owned by the user's
design teammate. `sprint/backlog/04-review-slice/frontend/00-port-design-tokens.md` is marked ⏸ Blocked.

## 3. Environment

macOS (darwin 25.6.0), zsh, Apple Silicon.

| Tool | State | Note |
|------|-------|------|
| Python | system 3.9.6 | **Too old.** `uv venv --python 3.11` fetches 3.11.15; both venvs already use it |
| uv | 0.11.30 | Manages both Python venvs |
| Node | v20.20.2, npm 10.8.2 | `apps/web/node_modules` installed |
| Docker | 29.6.2 | **Daemon was NOT running** this session — start Docker Desktop before `docker compose up` |
| Java | **absent** | Blocks Synthea. See § 7 |

**Ports:** web `3000`, API `8000`, Postgres `5432`.

**Secrets:** none in the repo. `apps/backend/.env.example` documents the contract; `.env` is
gitignored. Postgres dev credentials (`tilik`/`tilik`) are in `docker-compose.yml` and are
local-only throwaways.

**`.claude/` is gitignored** and must stay that way — it holds the user's office skills, and
this is a personal project. It contains `.claude/skills/bootstrap-project/scripts/init_boilerplate.sh`, which
carries an internal office host and API key. Verified never tracked. **Do not `git add -f` it.**

## 4. Build / run / test / verify

```bash
cd /Users/fahrialfiansyah121gmail.com/Documents/HEALTHKATHON-2026/tilik-klaim

# --- Verify everything (the path to run before and after any change) ---
(cd apps/backend   && uv run pytest)        # expect: 64 passed
(cd packages/domain && uv run pytest)       # expect: 21 passed
(cd apps/web       && npx tsc --noEmit)     # expect: silent
(cd apps/web       && npx rsbuild build)    # expect: ~165 kB total

# --- First-time setup on a fresh clone ---
(cd packages/domain && uv venv --python 3.11 && uv pip install -e ".[dev]")
(cd apps/backend    && uv venv --python 3.11 && uv pip install -e ".[dev]" && uv pip install -e ../../packages/domain)
(cd apps/web        && npm install)

# --- Run ---
open -a Docker && sleep 20          # daemon must be up first
docker compose up -d db             # Postgres on 5432
(cd apps/backend && uv run uvicorn app.main:app --reload)   # :8000, /docs, /healthz
(cd apps/web && npm run dev)                                 # :3000

# --- Regenerate committed artifacts (deterministic; a diff means something changed) ---
(cd apps/backend && uv run python tests/fixtures/build_gold.py)   # 5 gold fixtures
(cd apps/backend && uv run python tests/fixtures/build_api.py)    # 10 API fixtures
(cd apps/backend && uv run python -c "
import json,pathlib; from app.main import app
pathlib.Path('../../docs/api/openapi.json').write_text(
    json.dumps(app.openapi(), indent=2, sort_keys=True)+'\n')")
```

**Verify a contract change:** re-run the two builders, then `git diff` the fixtures. If the
diff is unintended, the contract moved without anyone deciding to move it.

## 5. Conventions & gotchas

**Project rules**

- Commits: Conventional Commits. Do **not** push without asking — the remote is public.
- Component placement (`.claude/rules/architecture.md`): domain components go in
  `src/features/{domain}/{feature}/components/`, never bare `src/components/`. Navigation is
  config-driven in `src/config/menu/*` — layouts must not hardcode route arrays.
- Naming: **code identifiers English, user-facing text Indonesian.** `apps/web/src/pages/queue/QueuePage.tsx`
  renders `<h1>Antrean Review</h1>`. Screen ids in `design/flow.json` must stay identical to
  `APP_MENU` ids in `apps/web/src/config/menu/app-menu.ts`.
- Sprint closure: when a task is done, tick every `## TODOs` box, set the top-of-file
  `**Status:** ✅ Done`, and append to `changelog/{web,backend}.md`. The header is the source of
  truth — a ticked checklist under a `📋 Planned` header does not count.
- Style: immutable models (`frozen=True`), files 200–400 lines, functions under 50, no magic
  numbers, errors handled explicitly.

**Traps already hit this session — do not repeat**

| Trap | What happened | Fix |
|------|---------------|-----|
| `cat > file` on an unread file | Overwrote `.gitignore` and dropped its `.claude` entry, nearly committing office skills to a public repo | **Read a file before overwriting it.** Use append or a targeted edit when adding |
| Office scaffold service | `.claude/skills/bootstrap-project/scripts/init_boilerplate.sh` POSTs to an internal office host, unreachable here (connection timeout), and `unzip -o` would **overwrite `apps/`** | **Never run it.** Apps were scaffolded by hand |
| Leakage test matched its own docstring | Test asserted terms against the whole JSON schema, including descriptions; the docstring explaining the rule contained "scenario" | Assert against **field names**, not serialized schema text |
| `model_fields` on an instance | Pydantic deprecation, removed in V3 | Access from the **class**: `CaseSummary.model_fields` |
| `timeout` command | Not present on macOS | Use `curl --max-time` / `--connect-timeout` |
| Route inspection | `app.routes` wraps included routers in `_IncludedRouter`; paths look missing | Inspect `app.openapi()["paths"]` instead |
| `grep -E` with `\|` | ERE uses bare `|`; `\|` silently matches nothing and looks like a real failure | Use `|` with `-E` |

**Architectural decisions already made — do not silently revisit**

- **Plain Postgres, not Supabase.** `.claude/rules/architecture.md` mandates Supabase, but
  `docs/canonical/03_architecture.md` § Component rationale specifies "PostgreSQL with JSONB",
  and this product needs no Auth/Storage/Realtime (roles are simulated). User confirmed.
  Reversible — self-hosted Supabase is Postgres plus services.
- **Tailwind and shadcn deliberately not installed**, pending `design/tokens.css` from the
  design team. Shell classes are Tailwind-shaped but inert. User confirmed: keep waiting.
- **Routes answer `501`** naming their implementing task, rather than returning fake data. A
  fixture served from a live endpoint looks like success and misleads.
- **10 evidence edge types, not 9.** One canonical bullet describes two distinct relations
  (`AUTHORED_BY`, `PART_OF_ENCOUNTER`).

## 6. Next steps

1. **`03-evidence-rules` — highest value, unblocked, closes Gate G4 (5 Sep).**
   `sprint/backlog/03-evidence-rules/backend/01-evidence-graph.md`, then `02-rule-engine.md`
   in the same folder. Gold fixtures already exist,
   so this needs no Synthea. Target: the phantom fixture screens to
   `LINE_WITHOUT_COMPLETED_PROCEDURE` with resolvable evidence, and the clean fixture produces
   no reason.
2. **`sprint/backlog/02-ingest-validation/backend/01-bundle-ingestion.md`** — needs Postgres up. Watch the
   partial-bundle edge case: it resolves to *valid-with-notes*, never *invalid*.
3. **`sprint/backlog/04-review-slice/frontend/`** — can start **now, in parallel**, against
   `apps/backend/tests/fixtures/api/*.json`. No running backend required.
4. **Sprint 01 remainder** — only after Java + Synthea are installed. Needed for G3's statistical
   scale (1.000 claims / 200 injections), not for proving the engine works.
5. Then: `05-ranking-models` → `06-evaluation-report` → `07-demo-hardening`.

Sprints 01 and 02 are still in `sprint/backlog/` despite being in progress. Promoting them to
`sprint/active/` is the user's call.

## 7. Blockers / decisions for the user

**1. ✅ Office host purged from public git history (was Blocker #1).**
An internal office host and port appeared in two commits, both pushed to a **public** GitHub
repo. **Resolved 2026-08-30:** history was rewritten to purge the value from every commit and
force-pushed, at the user's explicit instruction. A pre-rewrite backup is kept locally at
branch `backup/pre-rewrite-20260830` and tag `pre-rewrite-20260830`; delete them once you are
satisfied, since they still contain the original value.

The office API key (`void-daemon`) was **never** tracked — it lives only in gitignored
`.claude/`, confirmed by `git ls-files`. If any collaborator cloned or forked between the
original push and the rewrite, their copy still carries the old history.

**2. Java + Synthea not installed.** Blocks the three remaining Sprint 01 tasks and therefore
Gate G3's statistical scale. Requires a JDK plus a ~200 MB download. Not on the critical path
for G4 — the gold fixtures cover that.

**3. `design/tokens.css` and mockups** — owed by the user's design teammate. Until they land,
`sprint/backlog/04-review-slice/frontend/00-port-design-tokens.md` stays ⏸ Blocked and the UI renders unstyled.

**4. Gate G3 kill criteria fall due 2 Sep 18:00.** Two of the five in
`docs/canonical/01_product_decision.md` resolve then: if published fields cannot support three
modes, or the generator is not reproducible, the plan says switch to the backup solution
(RujukTepat). **Someone must call this explicitly at that hour.** Letting it slide silently is
the most expensive failure mode in the plan.

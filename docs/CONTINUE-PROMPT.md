# Continuation Prompt — paste into a fresh session

Copy everything in the block below as the first message to the new agent.

---

You are continuing **TilikKlaim** — a claim-evidence integrity layer that screens synthetic
SATUSEHAT-shaped JKN claim bundles for four facility risk patterns and requires a logged human
disposition. Healthkathon 2026 entry, category *Efisiensi Risiko pada Fasilitas Kesehatan*;
proposal due **19 September 2026** (internal upload target 18 Sep).

WORK DIR: `/Users/fahrialfiansyah121gmail.com/Documents/HEALTHKATHON-2026/tilik-klaim`
(git branch `development`, 18 commits, HEAD `3c661e7`, in sync with a PUBLIC GitHub remote.
**Do NOT push.** Commit your own work in small Conventional Commits as you finish each piece —
the owner reviews the log in the morning. Leave `scripts/dev.sh` alone; that modification is
theirs, in progress.)

FIRST, read these in order (do not skip):
1. `docs/HANDOVER.md` — full state, environment, verified commands, every trap already hit,
   and § 7 blocker 1, which you must resolve before anything else
2. `sprint/backlog/05-ranking-models/sprint.md` — the sprint, its acceptance, and the removal
   clause
3. `sprint/backlog/05-ranking-models/backend/01-similarity-anomaly.md` — your task, 25 TODOs
4. `docs/canonical/05_model_card.md` § Feature families, § Risk aggregation, § Model/version
   artifacts — the formula and all three caps are specified there **verbatim**; they are not
   design decisions for you to make
5. `docs/canonical/decisions/ADR-0002-no-llm-in-risk-score.md`
6. `packages/data/build/DATA_CARD.md` and `manifest.json` — the corpus you are modelling
7. `docs/qa/MANUAL-QA.md` — what the owner checks by eye, if any screen changes

KEY FACTS:
- **Stack:** Python 3.11 + FastAPI + Pydantic v2 + SQLAlchemy Core (`apps/backend`), React 18 +
  TS + Rsbuild + Tailwind v4 + shadcn/ui + Zustand (`apps/web`), Postgres 16 via Docker, shared
  `packages/domain`, generator in `packages/data`, and `packages/model` — an **empty placeholder
  you will populate**. `uv` manages Python; system Python is 3.9 and too old.
- **`scikit-learn>=1.5` and `pandas>=2.2` are already declared** in `apps/backend/pyproject.toml`.
  For `packages/model/pyproject.toml`, copy the shape of `packages/data/pyproject.toml` — it
  shows the `[tool.uv.sources]` editable-path pattern for depending on `tilik-domain`.
- **Run everything:** `./scripts/dev.sh --db`, then seed once with
  `(cd apps/backend && uv run python scripts/seed_dev.py)`. Sprint 05 is backend-and-package
  work, so you mostly will not need the servers up.
- **Verify after every change — all six, and report the counts:**
  `(cd apps/backend && uv run pytest)` → 312 · `(cd packages/domain && uv run pytest)` → 23 ·
  `(cd packages/data && uv run pytest)` → 47 · `(cd apps/web && npx tsc --noEmit)` → silent ·
  `(cd apps/web && npm test)` → 91 · `(cd apps/backend && uv run ruff check app tests)`.
  Add `(cd packages/model && uv run pytest)` once that package exists.
- **`uv run pytest` empties the dev database.** Re-seed with `scripts/seed_dev.py` afterwards.
- **Sprints 00–04 are done.** All three operator screens are live against the real API; six of
  seven endpoints work, and only `GET /v1/evaluations/{run_id}` still answers 501 (sprint 06).
- **The ethical core is in the types and asserted by tests, not a style preference.** The system
  reports "risiko atau anomali yang perlu ditinjau" — never fraud, never a rejection, never a
  payment action, never a sanction. Red is only for deterministic conflict; green only for a
  completed, validated action, and green never marks a claim safe. A case with no signal reads
  "tidak ada risiko teramati", never "bersih" or "aman".

RULES: Code identifiers in English, user-facing text in Indonesian. Immutable models
(`frozen=True`), files 200–400 lines, functions under 50, no magic numbers, explicit error
handling. **TDD: write the failing test first, then the implementation.** When the task
completes, tick every `## TODOs` box, set the top-of-file `**Status:** ✅ Done` (the header is
the source of truth), append to `changelog/backend.md`, and flip sprint 05 in
`sprint/01-sprint-planning.md`. Completed sprints stay in `sprint/backlog/` in this repo — do
not create `active/` or `archive/` folders. **Read any file before overwriting it.** Never run
`.claude/skills/bootstrap-project/scripts/init_boilerplate.sh`. Do not fill `sqlalchemy.url` in
`alembic.ini`. Regenerate `docs/api/openapi.json` with
`(cd apps/backend && uv run python scripts/export_openapi.py)` if you touch a router or DTO.

**Pre-authorised, so you do not stop to ask:** creating `packages/model/` and its
`pyproject.toml`; adding Python dependencies that are additive (`scipy`, `datasketch`, `joblib`);
adding backward-compatible query parameters to existing endpoints, with tests, never changing a
wire model. **Not pre-authorised:** re-freezing the corpus split (see the first task below), any
LLM or GNN in the risk path, and pushing to the remote.

NEXT TASK, in order:

**(a) Fix `packages/data/build/` first — it blocks everything else.** `pipeline.write_artifacts()`
writes `result.corpus.bundles`, the corpus **before** `strip_injector_traces()` runs. So the
published `corpus.json` still carries the injector tell (120 of 1,120 ids look like
`BND-00008-U798`, announcing which injector touched them), while `split.json` holds the *renamed*
ids and therefore shares **zero** overlap with the corpus or the labels. The leakage probe
reported `leakage_passed: true` because it ran on `cleaned`, which never reached disk.
`write_artifacts` has no test. Confirm it yourself:

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

Write the failing test first (the three files must join, and no published id may carry an
injector suffix), then fix the writer and carry the rename through the labels. **One decision is
the owner's, so stop and ask before regenerating:** re-running the pipeline changes
`test_set_digest`, and sprint 01's gate evidence quotes the current one. Re-freezing a split that
was announced as frozen is a reproducibility claim to make deliberately. Do the code and the test
now; leave the regeneration until they answer, and say clearly in your summary that you are
waiting on it.

**(b) Then sprint 05 — `01-similarity-anomaly.md`.** Six feature families, a TF-IDF character
n-gram or MinHash similarity baseline, an Isolation Forest or LOF anomaly baseline, band
calibration **on validation data only**, and a model card. The aggregation is fixed:
`priority = max(deterministic_priority, calibrated_similarity, calibrated_anomaly)`, with three
caps that already exist in the rules layer and must survive — no high band from text similarity
alone; missing evidence plus an incomplete bundle lowers certainty toward *request evidence*; an
exact duplicate fingerprint is high priority and still human-reviewed. Store every component
score and version, not just the aggregate. Exclude demographics and protected characteristics —
they are not needed for the four modes.

Five tests carry this task; write them first: group-split enforcement (training never sees test
participants or provider-time blocks), serialization round-trip (a saved model reloads and
reproduces identical predictions), feature-schema conformance, the **leakage probe** (no injector
metadata reachable from any feature), and threshold boundaries.

**The kill criterion is a designed outcome, not a failure.** If the hybrid adds no measurable
value over rules-only, the ML layer is removed and TilikKlaim ships rules-only —
`docs/canonical/01_product_decision.md` says *"this is not a product kill."* So build for a clean
revert: keep the model behind one call site, and do not let its scores reach a wire model until
sprint 06 has measured that they earn it. Do not tune until something looks better.

Afterwards, in order: sprint 06 (evaluation report — the last 501, plus the `/evaluation`
screen), then sprint 07 (demo hardening, which owns the demo/reset route).

Verify each change by running the six commands above and reporting the pass counts; for anything
that changes a screen, also load it at <http://localhost:3000> against a seeded database, save
screenshots of every state into `docs/qa/<date>-<screen>/`, and append a numbered click-through
to `docs/qa/MANUAL-QA.md`. Confirm you've read the docs above, then proceed.

---

# Task 01 — Audit and evaluation page

**Stack:** frontend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** ✅ Done
**Foundation:** no
**Autonomous:** yes
**Depends on:**
- [`../backend/01-evaluation-runner.md`](../backend/01-evaluation-runner.md) — reads its artifacts

## Goal

Show the measured evidence and its limitations, reading artifacts rather than computing
anything.

## Files to touch

- `apps/web/src/pages/evaluation/EvaluationPage.tsx`
- `apps/web/src/features/review/evaluation/components/`

## Skills to consult

- `sprint/00-app-spec.md` § 6 — widgets 1–9 and the four binding display rules
- `brief/05_AUDIT_EVALUASI.md` § 2

## TODOs

- [x] Version card: dataset, generator, model, ruleset versions plus dataset hash
- [x] Prominent synthetic-data badge
- [x] Baseline comparison table across the four approaches
- [x] Per-mode precision / recall / F1
- [x] False-positives-per-100-clean-claims chart
- [x] Precision-at-review-budget chart
- [x] p50 and p95 latency
- [x] **Limitations card, copy-ready** — never omitted, even under deadline pressure
- [x] **Display only** — no threshold tuning, no what-if control, no live experiment
- [x] Chart values read the same artifact as the tables
- [x] **Edge case — no evaluation run yet:** state that plainly and show the command to run; **never** render zeros
- [x] **Test — component:** the no-run-yet state renders distinctly from a zero-valued result
- [x] **Test:** rendered chart values match `metrics.json`

## Done when

The page renders from `evaluation/artifacts/`, every chart value matches `metrics.json`, the
limitations card is present and copyable, and the no-run-yet state is visually distinct from
a genuine zero.

## Closing checklist

- [x] All `## TODOs` items above are `[x]`
- [x] Done-when assertion verified
- [x] Top-of-file header literally reads `**Status:** ✅ Done`
- [x] Changelog entry appended to `changelog/web.md`

## Notes

**Files delivered.** `apps/web/src/features/review/evaluation/`: `types.ts`, `api.ts`,
`labels.ts`, `format.ts`, `selectors.ts`, `useEvaluation.ts`, `test-fixtures.ts`, and
`components/` — `SyntheticBadge`, `VersionCard`, `MetricTable`, `MetricBarChart`, `LatencyCard`,
`LimitationsCard`, `EvaluationPlaceholders`. Page at `src/pages/evaluation/EvaluationPage.tsx`.
13 new tests; the suite is 104.

**Charts and tables cannot disagree by construction.** Both are built by `selectors.ts` from one
response and both render through `format.ts`, so a mismatch could not be a rounding difference —
it would have to be a genuine integrity defect, which is what display rule 2 exists to catch.

**Four baselines and four modes are always listed**, in canonical order, whether or not the
response carries them. Iterating the response instead would make an unmeasured baseline silently
vanish from the comparison. A missing row renders *tidak terukur*, never a zero.

**`absent` is a distinct status from `failed`.** "Nothing has been run" and "the service is down"
both produce an empty page and lead to different next actions — a command versus a retry.
`useEvaluation` branches on the API's `EVALUATION_RUN_NOT_FOUND` code rather than on the status
alone.

**Widget 6 is a baseline comparison, not a budget sweep.** § 6 describes it as *ketepatan pada
berbagai besaran kapasitas*. The frozen `EvaluationResponse` carries precision at a single fixed
budget and has no field for a curve, so the page compares the four baselines at that budget. The
sweep would need a wire-model change; flagged for the owner rather than taken unilaterally.

**Three defects found only by opening the page** — all three passed the compiler, the 104 unit
tests, and a read-through. Recorded in `docs/qa/MANUAL-QA.md` § 1d: case counts rendered as
`7.0000`, the limitations card rendered in English on an Indonesian screen, and the manifest's
English `threshold_logic` string printed raw into the version card.

# Task 01 — Audit and evaluation page

**Stack:** frontend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** 📋 Planned
**Foundation:** no
**Autonomous:** yes
**Depends on:**
- [`../backend/01-evaluation-runner.md`](../backend/01-evaluation-runner.md) — reads its artifacts

## Goal

Show the measured evidence and its limitations, reading artifacts rather than computing
anything.

## Files to touch

- `apps/web/src/pages/evaluasi/EvaluasiPage.tsx`
- `apps/web/src/features/review/evaluation/components/`

## Skills to consult

- `sprint/00-app-spec.md` § 6 — widgets 1–9 and the four binding display rules
- `brief/05_AUDIT_EVALUASI.md` § 2

## TODOs

- [ ] Version card: dataset, generator, model, ruleset versions plus dataset hash
- [ ] Prominent synthetic-data badge
- [ ] Baseline comparison table across the four approaches
- [ ] Per-mode precision / recall / F1
- [ ] False-positives-per-100-clean-claims chart
- [ ] Precision-at-review-budget chart
- [ ] p50 and p95 latency
- [ ] **Limitations card, copy-ready** — never omitted, even under deadline pressure
- [ ] **Display only** — no threshold tuning, no what-if control, no live experiment
- [ ] Chart values read the same artifact as the tables
- [ ] **Edge case — no evaluation run yet:** state that plainly and show the command to run; **never** render zeros
- [ ] **Test — component:** the no-run-yet state renders distinctly from a zero-valued result
- [ ] **Test:** rendered chart values match `metrics.json`

## Done when

The page renders from `evaluation/artifacts/`, every chart value matches `metrics.json`, the
limitations card is present and copyable, and the no-run-yet state is visually distinct from
a genuine zero.

## Closing checklist

- [ ] All `## TODOs` items above are `[x]`
- [ ] Done-when assertion verified
- [ ] Top-of-file header literally reads `**Status:** ✅ Done`
- [ ] Changelog entry appended to `changelog/web.md`

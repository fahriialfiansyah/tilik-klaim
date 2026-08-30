# Task 03 — Grouped split, leakage controls, and data card

**Stack:** backend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** 📋 Planned
**Foundation:** no
**Autonomous:** no — offline generation run by an engineer on demand.
**Depends on:**
- [`./02-risk-injectors.md`](./02-risk-injectors.md) — split and leakage checks run on the injected corpus

## Goal

Split the corpus so related records cannot cross partitions, strip every trace the injectors
left behind, and prove the result is not leaking labels.

## Files to touch

- `packages/data/src/split.py` — grouped split by participant and provider-time block
- `packages/data/src/leakage.py` — trivial-classifier leakage probe
- `packages/data/src/data_card.py` — data-card generator
- `packages/data/tests/test_leakage.py` — leakage probe assertions
- `packages/data/tests/test_split.py` — partition-isolation assertions

## Skills to consult

- `docs/canonical/04_data_card.md` § Train/validation/test split, § Leakage controls, § Data card acceptance criteria

## TODOs

- [ ] Split 60% train, 20% validation, 20% test
- [ ] Split **first** by participant and provider-time block so related records cannot cross partitions
- [ ] Fit unsupervised detectors primarily on clean training records
- [ ] Use validation injections for threshold selection only, never for fitting
- [ ] Freeze the test set before any tuning; make the freeze explicit and checkable
- [ ] Keep the five gold demo fixtures **outside** all metric calculation
- [ ] Leakage control: remove injection manifests from feature tables
- [ ] Leakage control: remove sequential injected IDs
- [ ] Leakage control: remove mutation timestamps
- [ ] Leakage control: regenerate identifiers and serialization order after injection
- [ ] **Leakage probe:** train a trivial classifier on IDs and ordering alone
- [ ] **Leakage probe assertion:** near-perfect performance is an **alarm** that halts evaluation, not a pass
- [ ] Avoid random row split; assert the split is grouped and temporal
- [ ] **Test — split isolation:** no participant and no provider-time block appears in two partitions
- [ ] **Test — demo separation:** none of the five gold fixtures appears in any metric set
- [ ] Data card: source, license/terms, generation version, schema, population, injection logic, split logic, missingness, known biases, prohibited uses
- [ ] Data card: the mandatory sentence — *"This dataset is synthetic and does not represent JKN prevalence or real provider behavior."*
- [ ] **Edge case — rounding:** tolerance documented in the data card

## Done when

The leakage probe scores no better than chance; no participant or provider-time block spans
two partitions; the five gold fixtures are provably absent from every metric set; and the
data card carries all eleven required elements plus the mandatory sentence.

> If the leakage probe fires, **stop**. Report no metric until it passes. Impressive numbers
> from self-made data almost always mean the model found the injector's fingerprints.

## Closing checklist

- [ ] All `## TODOs` items above are `[x]`
- [ ] Done-when assertion verified
- [ ] Top-of-file header literally reads `**Status:** ✅ Done`
- [ ] Changelog entry appended to `changelog/backend.md`

## Notes

This task is the last line of defence before fabricated-looking numbers reach the proposal.
Under deadline pressure it is the most tempting task to shorten, and the most expensive one
to have skipped — a single sharp question from a judge unravels everything built on it.

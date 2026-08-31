# Task 03 — Grouped split, leakage controls, and data card

**Stack:** backend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** ✅ Done
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

- [x] Split 60% train, 20% validation, 20% test
- [x] Split **first** by participant and provider-time block so related records cannot cross partitions
- [x] Fit unsupervised detectors primarily on clean training records
- [x] Use validation injections for threshold selection only, never for fitting
- [x] Freeze the test set before any tuning; make the freeze explicit and checkable
- [x] Keep the five gold demo fixtures **outside** all metric calculation
- [x] Leakage control: remove injection manifests from feature tables
- [x] Leakage control: remove sequential injected IDs
- [x] Leakage control: remove mutation timestamps
- [x] Leakage control: regenerate identifiers and serialization order after injection
- [x] **Leakage probe:** train a trivial classifier on IDs and ordering alone
- [x] **Leakage probe assertion:** near-perfect performance is an **alarm** that halts evaluation, not a pass
- [x] Avoid random row split; assert the split is grouped and temporal
- [x] **Test — split isolation:** no participant and no provider-time block appears in two partitions
- [x] **Test — demo separation:** none of the five gold fixtures appears in any metric set
- [x] Data card: source, license/terms, generation version, schema, population, injection logic, split logic, missingness, known biases, prohibited uses
- [x] Data card: the mandatory sentence — *"This dataset is synthetic and does not represent JKN prevalence or real provider behavior."*
- [x] **Edge case — rounding:** tolerance documented in the data card

## Done when

The leakage probe scores no better than chance; no participant or provider-time block spans
two partitions; the five gold fixtures are provably absent from every metric set; and the
data card carries all eleven required elements plus the mandatory sentence.

> If the leakage probe fires, **stop**. Report no metric until it passes. Impressive numbers
> from self-made data almost always mean the model found the injector's fingerprints.

## Closing checklist

- [x] All `## TODOs` items above are `[x]`
- [x] Done-when assertion verified
- [x] Top-of-file header literally reads `**Status:** ✅ Done`
- [x] Changelog entry appended to `changelog/backend.md`

## Notes

This task is the last line of defence before fabricated-looking numbers reach the proposal.
Under deadline pressure it is the most tempting task to shorten, and the most expensive one
to have skipped — a single sharp question from a judge unravels everything built on it.

## Notes

**The split assigns groups by hashing, not by shuffling.** A group lands in the same partition
regardless of corpus size or ordering, so adding records cannot silently move an existing group
across a boundary and invalidate a measurement already taken. A test asserts that stability.

**Freezing the test set is only a control if a violation is detectable.** `make_split` records a
digest of the test partition and `assert_test_set_unchanged` re-checks it, so a change raises
rather than passing unnoticed. A promise not to touch it would not be a control.

**The leakage probe is tested against a planted leak.** A probe that never fires proves nothing,
so `test_probe_detects_a_planted_leak` sorts the corpus by injection status and asserts the probe
catches it. Only then does a clean result mean anything.

Raw injector output *does* leak: ids like `BND-00042-R173` announce both that a record was
injected and which injector did it. `strip_injector_traces` regenerates every identifier and
reorders the corpus by the new ids; the probe then confirms the tell is gone.

Measured at G3 scale: probe accuracy 0.687 against a 0.686 baseline — margin **+0.0009**, well
inside the 0.10 tolerance. The corpus is not answerable from identifiers or ordering.

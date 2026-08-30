# Task 02 — Four risk-pattern injectors with ground-truth labels

**Stack:** backend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** 📋 Planned
**Foundation:** no
**Autonomous:** no — offline generation run by an engineer on demand.
**Depends on:**
- [`./01-synthea-adapter.md`](./01-synthea-adapter.md) — injection happens **after** a clean episode is verified

## Goal

Inject the four official risk patterns into verified-clean episodes and record injection
ground-truth labels rich enough to evaluate detection objectively.

## Files to touch

- `packages/data/src/injectors/phantom.py` — billed line without completed supporting event
- `packages/data/src/injectors/repeat.py` — second claim, overlapping lines, changed IDs
- `packages/data/src/injectors/clone.py` — narrative or service sequence copied across encounters
- `packages/data/src/injectors/unbundling.py` — one episode split across adjacent claims
- `packages/data/src/injectors/labels.py` — injection label record
- `packages/data/tests/test_injector_invariants.py` — one invariant test per injector

## Skills to consult

- `docs/canonical/04_data_card.md` § Injected patterns and § Labels
- `docs/canonical/05_model_card.md` § Detector design by mode — the evidence each mode must surface

## TODOs

- [ ] Verify the clean state **before** injecting; abort if the base corpus is inconsistent
- [ ] Phantom injector: add a billed procedure or drug line with no completed matching event, or mark evidence entered-in-error
- [ ] Repeat injector: second claim for the same participant/provider/episode with overlapping lines; change IDs and small non-material fields
- [ ] Clone injector: copy or lightly alter narrative or service sequence across different participants or encounters
- [ ] Unbundling injector: split a coherent episode's services into temporally adjacent claims
- [ ] Label record per injection: `injection_id`, type, source clean record, target record(s), injector version, seed
- [ ] Label record: expected violated invariants and expected evidence references
- [ ] Label record: difficulty level — obvious, moderate, subtle
- [ ] Label record: multi-label status
- [ ] Label record: flag excluding injector-only metadata from model features
- [ ] Target ~300 cases per mode; ≥200 injections total at Gate 3
- [ ] **Test — per-injector invariant:** each injector makes the rule it targets actually fire
- [ ] **Edge case — multi-label injections:** allowed, flagged, proportion capped and documented
- [ ] **Edge case — duplicate IDs after injection:** detected and rejected
- [ ] Naming discipline: these are **injection ground-truth labels**, never "fraud labels" — in code, docs, and proposal

## Done when

At least 200 injections exist across the four modes; each injector's invariant test proves
the targeted rule fires; every label carries its expected evidence references and difficulty
level; and the multi-label proportion is capped and documented.

## Closing checklist

- [ ] All `## TODOs` items above are `[x]`
- [ ] Done-when assertion verified
- [ ] Top-of-file header literally reads `**Status:** ✅ Done`
- [ ] Changelog entry appended to `changelog/backend.md`

## Notes

Injected prevalence is a **test-design choice**. It must never be described as JKN
prevalence — in code comments, in the data card, or in the deck.

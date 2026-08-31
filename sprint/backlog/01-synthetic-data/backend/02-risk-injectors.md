# Task 02 — Four risk-pattern injectors with ground-truth labels

**Stack:** backend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** ✅ Done
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

- [x] Verify the clean state **before** injecting; abort if the base corpus is inconsistent
- [x] Phantom injector: add a billed procedure or drug line with no completed matching event, or mark evidence entered-in-error
- [x] Repeat injector: second claim for the same participant/provider/episode with overlapping lines; change IDs and small non-material fields
- [x] Clone injector: copy or lightly alter narrative or service sequence across different participants or encounters
- [x] Unbundling injector: split a coherent episode's services into temporally adjacent claims
- [x] Label record per injection: `injection_id`, type, source clean record, target record(s), injector version, seed
- [x] Label record: expected violated invariants and expected evidence references
- [x] Label record: difficulty level — obvious, moderate, subtle
- [x] Label record: multi-label status
- [x] Label record: flag excluding injector-only metadata from model features
- [x] Target ~300 cases per mode; ≥200 injections total at Gate 3
- [x] **Test — per-injector invariant:** each injector makes the rule it targets actually fire
- [x] **Edge case — multi-label injections:** allowed, flagged, proportion capped and documented
- [x] **Edge case — duplicate IDs after injection:** detected and rejected
- [x] Naming discipline: these are **injection ground-truth labels**, never "fraud labels" — in code, docs, and proposal

## Done when

At least 200 injections exist across the four modes; each injector's invariant test proves
the targeted rule fires; every label carries its expected evidence references and difficulty
level; and the multi-label proportion is capped and documented.

## Closing checklist

- [x] All `## TODOs` items above are `[x]`
- [x] Done-when assertion verified
- [x] Top-of-file header literally reads `**Status:** ✅ Done`
- [x] Changelog entry appended to `changelog/backend.md`

## Notes

Injected prevalence is a **test-design choice**. It must never be described as JKN
prevalence — in code comments, in the data card, or in the deck.

## Notes

The invariant tests found two injectors whose labels were wrong, and both corrections improved
the design.

**Repeat billing produces two shapes, not one.** The first version copied the encounter for every
difficulty, so the duplicate's fingerprint matched exactly — and the engine correctly emitted
`DUPLICATE_CLAIM_FINGERPRINT` while the label demanded `OVERLAPPING_CLAIM_SAME_EPISODE`. The
engine was right. An *obvious* repeat is now a verbatim resubmission expecting the fingerprint
reason; *moderate* and *subtle* bill the same services at a **new encounter**, which is what a
second visit looks like, and expect the weaker overlap reason.

**A clone that cannot be recognised is not a clone.** Two substitutions dropped three subtle
injections to 0.659–0.688 similarity, below the detector's reporting threshold, so their labels
claimed a rule would fire that could not. Subtle now makes one substitution and the injector
enforces `MINIMUM_RETAINED_SIMILARITY`, refusing to inject into a note too short to absorb the
change. Every label is now truthful by construction rather than by luck.

**The clone injector requires two participants at one provider.** Copying a note within one
patient's own record would produce a case the clone detector is not looking for — and would have
concealed the scoping defect this project already hit once.

Achieved at G3 scale: 240 injections, 60 per mode across all four, realised multi-label ratio
0.067. Every injector's invariant test passes at all three difficulty levels.

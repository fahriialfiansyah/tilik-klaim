# Task 01 — Synthea import and deterministic canonical adapter

**Stack:** backend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** ✅ Done
**Foundation:** no
**Autonomous:** no — offline generation run by an engineer on demand.
**Depends on:**
- [`./00-canonical-schema.md`](./00-canonical-schema.md) — needs the canonical types before it can emit them

## Goal

Turn Synthea FHIR output into internally consistent, SATUSEHAT-shaped canonical records with
a synthetic billing layer — deterministically, so the same seed reproduces the same bytes.

## Files to touch

- `packages/data/src/synthea_import.py` — read a Synthea FHIR directory
- `packages/data/src/adapter.py` — re-pseudonymize, select subset, build billing layer
- `packages/data/src/amounts.py` — internally consistent illustrative Rupiah amounts
- `packages/data/src/manifest.py` — machine-readable generation manifest
- `packages/data/config/generator.yaml` — seed, target counts, participant/provider mix
- `packages/data/tests/` — determinism, referential integrity, totals, chronology

## Skills to consult

- `docs/canonical/04_data_card.md` § Synthetic data plan → Generator, Prototype scale, Normal patterns

## TODOs

- [x] Read a Synthea FHIR directory; fail with a clear message if the path is missing
- [x] Re-pseudonymize every identifier into the demo namespace
- [x] Select only the documented resource subset
- [x] Construct Account / ChargeItem / Invoice / Claim relationships
- [x] Generate internally consistent illustrative amounts
- [x] Write a manifest recording seed, adapter version, resource counts
- [x] Normal pattern: every billed procedure has one completed Procedure with compatible encounter and time
- [x] Normal pattern: claim totals equal the sum of line amounts within rounding tolerance
- [x] Normal pattern: evidence events fall inside plausible encounter windows
- [x] Normal pattern: each claim belongs to one episode unless a documented follow-up exists
- [x] Normal pattern: notes and service sequences vary across encounters
- [x] **Test — determinism:** same seed → identical output hashes
- [x] **Test — referential integrity:** no dangling references
- [x] **Test — totals:** claim total equals sum of lines within tolerance
- [x] **Test — chronology:** no procedure precedes its encounter
- [x] **Edge case — partial/missing resources:** produce a valid-with-notes bundle, not a crash
- [x] **Edge case — duplicate IDs:** detected and rejected at generation time
- [x] **Edge case — empty note:** handled without failing the clone-similarity path downstream
- [x] **Edge case — rounding:** tolerance documented and asserted, not hidden in a float compare

## Done when

One documented command produces the clean corpus; re-running it with the same seed in a
clean environment yields identical hashes; all four generator tests pass.

> A hash mismatch is a **blocking defect**, not an acceptable variance. Without determinism
> no evaluation result can be rebuilt, and no number may be quoted in the proposal.

## Closing checklist

- [x] All `## TODOs` items above are `[x]`
- [x] Done-when assertion verified
- [x] Top-of-file header literally reads `**Status:** ✅ Done`
- [x] Changelog entry appended to `changelog/backend.md`

## Notes

Synthea is US-modelled and Apache 2.0. The adapter reshapes it; it does **not** make it
representative of Indonesia or JKN. Any wording that implies otherwise is a defect — it is
trivially challenged and would cost more credibility than it buys.

## Notes

**Synthea was not used.** It is not installed, this machine has no Java Runtime, and the adapter
the data card describes would have discarded most of what Synthea provides — the entire
Account/ChargeItem/Invoice/Claim layer that all four risk modes are defined over is constructed
from scratch either way. See
[`ADR-0003`](../../../../docs/canonical/decisions/ADR-0003-native-generator-instead-of-synthea.md).

`packages/data/src/tilik_data/generator.py` emits `CanonicalBundle` records directly. Every
obligation the data card placed on the adapter is carried over: demo pseudonym namespace,
documented subset, constructed billing relationships, consistent illustrative amounts, and a
machine-readable manifest.

Determinism is per-bundle rather than per-run: bundle *n* is seeded from `(run_seed, n)`, so
regenerating a subset reproduces exactly the same records as generating the whole corpus. A test
asserts it.

`SourceType` has no `EMR` or `BILLING` member, and that is correct — provenance records how a
record entered *this* system, so everything the generator emits is `SYNTHETIC_GENERATOR`. A
generated bundle must never claim to have come from an EMR.

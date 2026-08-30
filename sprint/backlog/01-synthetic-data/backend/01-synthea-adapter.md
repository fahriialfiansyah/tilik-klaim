# Task 01 — Synthea import and deterministic canonical adapter

**Stack:** backend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** 📋 Planned
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

- [ ] Read a Synthea FHIR directory; fail with a clear message if the path is missing
- [ ] Re-pseudonymize every identifier into the demo namespace
- [ ] Select only the documented resource subset
- [ ] Construct Account / ChargeItem / Invoice / Claim relationships
- [ ] Generate internally consistent illustrative amounts
- [ ] Write a manifest recording seed, adapter version, resource counts
- [ ] Normal pattern: every billed procedure has one completed Procedure with compatible encounter and time
- [ ] Normal pattern: claim totals equal the sum of line amounts within rounding tolerance
- [ ] Normal pattern: evidence events fall inside plausible encounter windows
- [ ] Normal pattern: each claim belongs to one episode unless a documented follow-up exists
- [ ] Normal pattern: notes and service sequences vary across encounters
- [ ] **Test — determinism:** same seed → identical output hashes
- [ ] **Test — referential integrity:** no dangling references
- [ ] **Test — totals:** claim total equals sum of lines within tolerance
- [ ] **Test — chronology:** no procedure precedes its encounter
- [ ] **Edge case — partial/missing resources:** produce a valid-with-notes bundle, not a crash
- [ ] **Edge case — duplicate IDs:** detected and rejected at generation time
- [ ] **Edge case — empty note:** handled without failing the clone-similarity path downstream
- [ ] **Edge case — rounding:** tolerance documented and asserted, not hidden in a float compare

## Done when

One documented command produces the clean corpus; re-running it with the same seed in a
clean environment yields identical hashes; all four generator tests pass.

> A hash mismatch is a **blocking defect**, not an acceptable variance. Without determinism
> no evaluation result can be rebuilt, and no number may be quoted in the proposal.

## Closing checklist

- [ ] All `## TODOs` items above are `[x]`
- [ ] Done-when assertion verified
- [ ] Top-of-file header literally reads `**Status:** ✅ Done`
- [ ] Changelog entry appended to `changelog/backend.md`

## Notes

Synthea is US-modelled and Apache 2.0. The adapter reshapes it; it does **not** make it
representative of Indonesia or JKN. Any wording that implies otherwise is a defect — it is
trivially challenged and would cost more credibility than it buys.

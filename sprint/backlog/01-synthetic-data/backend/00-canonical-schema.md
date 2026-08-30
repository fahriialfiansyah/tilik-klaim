# Task 00 — Canonical model, reason-code catalog, and gold fixtures

**Stack:** backend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** ✅ Done
**Foundation:** yes
**Autonomous:** no — one-time schema definition consumed by every later task.

> **Foundation task.** Sprints 02, 03, 04, and 06 all read what this publishes. It must be
> `[x]` before any of them starts.

## Goal

Publish the canonical data model, the reason-code catalog, and five curated gold fixtures,
so every downstream stack codes against one agreed shape instead of inventing its own.

## Contract delivered

**1. Canonical model** — `packages/domain/src/` types covering all eleven domains in
`docs/canonical/04_data_card.md` § Minimum required schema: claim header, claim lines,
encounter, clinical conditions, procedures, medication, diagnostics, documents, billing
resources, provenance, review. Field names are the prototype's internal canonical model and
must **map to** published SATUSEHAT FHIR resources — not claim to reproduce them.

**2. Reason-code catalog** — one entry per reason the engine can emit:

| Field | Content |
|-------|---------|
| `code` | Stable identifier used by the UI and by tests |
| `sentence_id` | Human-readable working-language sentence |
| `mode` | One of the four risk modes |
| `required_evidence` | Resource types that must accompany this reason for it to be valid |
| `ruleset_version` | Version in force; historical results keep their own version |

**3. Evidence edge types** — the nine canonical edges in
`docs/canonical/03_architecture.md` § Canonical evidence edges. Every edge stores source
resource IDs, derivation rule, version, and confidence when inferred.

**4. Five gold fixtures** — clean, phantom, repeat, clone, unbundled. Committed to the repo
and **excluded from all metric computation**.

## Files to touch

- `packages/domain/src/tilik_domain/canonical.py` — canonical entity types
- `packages/domain/src/tilik_domain/reasons.py` — reason-code catalog
- `packages/domain/src/tilik_domain/edges.py` — evidence edge types and derivation metadata
- `packages/domain/src/tilik_domain/versioning.py` — ruleset/engine version helpers
- `apps/backend/tests/fixtures/gold/*.json` — five curated fixtures
- `apps/backend/tests/fixtures/build_gold.py` — deterministic fixture builder
- `packages/domain/tests/` — reason-catalog and edge-contract tests
- `docs/canonical/04_data_card.md` — cross-check only; **do not edit** (canonical, read-only)

## Skills to consult

- `docs/canonical/04_data_card.md` § Minimum required schema — the eleven domains
- `docs/canonical/03_architecture.md` § Canonical evidence edges — the nine edges
- `docs/canonical/05_model_card.md` § Detector design by mode — required explanation per mode

## TODOs

- [x] Canonical types for all eleven schema domains, with an explicit mapping note per domain
- [x] Reason-code catalog with a working-language sentence per code
- [x] Ten evidence edge types with source IDs, derivation rule, version, confidence
- [x] Version helpers so every case and audit event records ruleset and engine version
- [x] Gold fixture: clean — every billed line supported, totals reconcile, chronology sound
- [x] Gold fixture: phantom — one billed procedure line with no completed Procedure
- [x] Gold fixture: repeat — two claims, same participant/provider/episode, overlapping lines
- [x] Gold fixture: clone — narrative copied across different encounters
- [x] Gold fixture: unbundled — one coherent episode split across adjacent claims
- [x] Structural separation so the demo scenario label cannot reach detector features
- [x] Test: every gold fixture parses into canonical types with all references resolving
- [x] Test: the clean fixture produces **no** injected reason

## Done when

All five gold fixtures parse into the canonical model with every reference resolving; the
reason-code catalog covers every mode with a required-evidence list; and a test proves the
scenario label is structurally unreachable from feature tables.

## Closing checklist

- [x] All `## TODOs` items above are `[x]`
- [x] Done-when assertion verified
- [x] Top-of-file header literally reads `**Status:** ✅ Done`
- [x] Changelog entry appended to `changelog/backend.md`

## Notes

(Append-only.)

## Outcome — 2026-08-30

Delivered and verified. `packages/domain` is installable and imported by `apps/backend`.

| Artifact | Result |
|----------|--------|
| Canonical model | 11 domains, all frozen (`extra="forbid"`), pseudonymous only |
| Reason catalog | 7 codes across all 4 risk modes, each with a working-language sentence |
| Evidence edges | **10** types — see note below |
| Gold fixtures | 5 committed, references resolve, totals reconcile, chronology sound |
| Tests | 62 passing (41 in `apps/backend`, 21 in `packages/domain`) |

**Ten edge types, not nine.** The canonical doc lists nine bullets, but one of them —
*"Document AUTHORED_BY Practitioner and Document PART_OF Encounter"* — describes two distinct
relations with different targets. They are modelled separately as `AUTHORED_BY` and
`PART_OF_ENCOUNTER`. Same coverage, one more type.

**Confidence contract.** `POSSIBLE_DUPLICATE_OF` and `SIMILAR_TO` are inferred and *must*
carry a confidence; every other edge is stated in the source and must *not*. Both directions
raise at construction time, so an inferred edge can never present a guess as a fact.

**Leakage separation is structural.** `DemoMetadata` is a sibling of `CanonicalBundle`, never
a field on it, and `extra="forbid"` blocks smuggling one in at runtime.
`test_leakage_separation.py` asserts the field names, the serialized payload, and the runtime
rejection — three angles, because a filter someone has to remember is not a guarantee.

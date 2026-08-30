# Task 01 — Derive and persist the canonical evidence graph

**Stack:** backend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** ✅ Done
**Foundation:** no
**Autonomous:** yes
**Depends on:**
- [`../../02-ingest-validation/backend/01-bundle-ingestion.md`](../../02-ingest-validation/backend/01-bundle-ingestion.md) — for its *storage* layer only. Derivation itself needs no
  ingestion service: the five gold fixtures are already validated `CanonicalBundle`s, so the
  graph was built and tested against those. `app/store/edges.py` therefore defines the
  repository contract plus an in-memory implementation; the SQLAlchemy binding lands with
  ingestion, which owns the engine, session, and migrations.

## Goal

Turn a flat canonical bundle into a traceable evidence graph, so "what supports this billed
line?" always has an answer that resolves to source resources.

## Files to touch

- `apps/backend/app/service/evidence_graph.py` — edge derivation (NetworkX in-memory)
- `apps/backend/app/store/edges.py` — normalized edge persistence
- `apps/backend/tests/test_evidence_graph.py`

## Skills to consult

- `docs/canonical/03_architecture.md` § Canonical evidence edges — the nine required edges
- `brief/02_MESIN_BUKTI_DETEKSI.md` § 2.1 — the same nine edges in working language

## TODOs

- [x] Derive all nine canonical edges — all ten `EdgeType` members; the architecture doc's nine bullets cover ten types because one bullet carries both `AUTHORED_BY` and `PART_OF_ENCOUNTER`
- [x] Every edge stores source resource IDs, derivation rule, version, and confidence when inferred
- [x] Persist normalized edges; keep the working graph in memory
- [x] Episode grouping: claims linked into one episode unless a documented follow-up exists
- [x] **Test:** every edge on a gold fixture resolves to real source resources
- [x] **Test:** derivation is deterministic for the same bundle and version
- [x] **Edge case — incomplete bundle:** graph builds with gaps recorded, rather than failing

## Done when

All nine edge types derive on the gold fixtures, every edge resolves to real source
resources, and derivation is deterministic for a given bundle and version.

## Closing checklist

- [x] All `## TODOs` items above are `[x]`
- [x] Done-when assertion verified
- [x] Top-of-file header literally reads `**Status:** ✅ Done`
- [x] Changelog entry appended to `changelog/backend.md`

## Notes

`ResourceType` had no `PRACTITIONER` member, so `Document AUTHORED_BY Practitioner` — required
by `docs/canonical/03_architecture.md` — could not be constructed at all, even though the clone
fixtures already carry `author_id="PRACT-02"`. Added it to `packages/domain`, along with
`ResourceType.is_stored_resource`: episodes and practitioners are referenced by identity but
never stored in a bundle, and reference resolution has to tell that apart from a dangling ref.
This corrects the domain package to match the canonical architecture; no canonical doc changed.

Two similarity floors (`SIMILARITY_CANDIDATE_FLOOR`, `DUPLICATE_CANDIDATE_FLOOR`) decide only
whether an edge is *drawn*. They are candidate-generation floors, not risk thresholds — bands
and their calibration stay in the rule engine, per `docs/canonical/05_model_card.md`.

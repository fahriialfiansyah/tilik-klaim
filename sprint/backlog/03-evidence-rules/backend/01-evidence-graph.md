# Task 01 — Derive and persist the canonical evidence graph

**Stack:** backend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** 📋 Planned
**Foundation:** no
**Autonomous:** yes
**Depends on:**
- [`../../02-ingest-validation/backend/01-bundle-ingestion.md`](../../02-ingest-validation/backend/01-bundle-ingestion.md) — operates on validated canonical bundles

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

- [ ] Derive all nine canonical edges
- [ ] Every edge stores source resource IDs, derivation rule, version, and confidence when inferred
- [ ] Persist normalized edges; keep the working graph in memory
- [ ] Episode grouping: claims linked into one episode unless a documented follow-up exists
- [ ] **Test:** every edge on a gold fixture resolves to real source resources
- [ ] **Test:** derivation is deterministic for the same bundle and version
- [ ] **Edge case — incomplete bundle:** graph builds with gaps recorded, rather than failing

## Done when

All nine edge types derive on the gold fixtures, every edge resolves to real source
resources, and derivation is deterministic for a given bundle and version.

## Closing checklist

- [ ] All `## TODOs` items above are `[x]`
- [ ] Done-when assertion verified
- [ ] Top-of-file header literally reads `**Status:** ✅ Done`
- [ ] Changelog entry appended to `changelog/backend.md`

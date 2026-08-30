> Sumber: docs/HEALTHKATHON_2026_WINNING_MASTER_PLAN.docx §11
> Status: canonical — read-only. Perubahan hanya lewat ADR baru.

# ADR-0001 — Canonical model: PostgreSQL + JSONB, derived NetworkX evidence graph

- **Status:** Accepted
- **Scope:** Persistence and evidence-graph layer (components 3 and 4 of the architecture pipeline)
- **Owner section:** [03_architecture.md](../03_architecture.md)

**Cross-reference (jangan salin isinya ke sini):**

- Full component table, API contracts, and security posture → [03_architecture.md](../03_architecture.md)
- Field names of the internal canonical model → [04_data_card.md](../04_data_card.md)
- Detector inputs derived from these edges → [05_model_card.md](../05_model_card.md)

---

## Context

§11 defines the pipeline stage that this ADR governs:

```
3. Canonical episode and evidence graph
        ↓
4. Rules + similarity + anomaly scoring
```

§11 component rationale, verbatim:

| Component | Technology choice | Why it exists | What is deliberately avoided |
|---|---|---|---|
| Canonical store | PostgreSQL with JSONB for raw resources and relational canonical tables | Preserves source payload while enabling reliable queries and audit | Neo4j or distributed data platform before evidence requires it |
| Evidence graph | In-memory/derived graph using Python/NetworkX; normalized edges persisted | Makes Claim→line→encounter→clinical evidence traceable | GNN as a default model |
| Audit | Append-only review events in PostgreSQL | Reproducibility, accountability, later label quality | Editing historical decisions in place |

## Decision

1. Persist raw ingested resources as JSONB and the canonical entities as relational tables in **PostgreSQL**.
2. Build the evidence graph as an **in-memory/derived graph using Python/NetworkX**; persist the normalized edges.
3. Keep review events **append-only** in PostgreSQL.
4. Do **not** adopt Neo4j or a distributed data platform "before evidence requires it". Do **not** adopt a GNN as a default model.

## Canonical evidence edges (verbatim, §11)

At minimum, derive and test these edges:

- Claim SUPPORTS/CONTAINS ClaimLine
- ClaimLine BILLED_FROM ChargeItem
- Claim/ClaimLine FOR Encounter
- ClaimLine SUPPORTED_BY Procedure | MedicationDispense | Observation | DiagnosticReport
- Encounter HAS Condition | Procedure | Medication | Document
- Document AUTHORED_BY Practitioner and Document PART_OF Encounter
- Claim POSSIBLE_DUPLICATE_OF Claim
- Document SIMILAR_TO Document
- Claim PART_OF Episode

Every edge stores source resource IDs, derivation rule, version, and confidence if inferred.

## Consequences

- Source payload is preserved alongside queryable canonical tables, which §11 states is what enables "reliable queries and audit".
- Traceability of Claim→line→encounter→clinical evidence is a property of the derived graph, not of a graph database.
- Historical decisions are never edited in place; §16 requires that a changed disposition be recorded as "a superseding event; never overwrite history" → [07_privacy_threat_model.md](../07_privacy_threat_model.md).
- Reversing this ADR (for example, adopting Neo4j or a GNN) requires a new ADR.

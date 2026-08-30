> Sumber: docs/HEALTHKATHON_2026_WINNING_MASTER_PLAN.docx §11
> Status: canonical — read-only. Perubahan hanya lewat ADR baru.


# 03 — Technical Architecture

**Cross-reference (jangan salin isinya ke sini):**

- Canonical store & derived graph decision → [decisions/ADR-0001-canonical-model.md](decisions/ADR-0001-canonical-model.md)
- No-LLM-in-risk-score decision → [decisions/ADR-0002-no-llm-in-risk-score.md](decisions/ADR-0002-no-llm-in-risk-score.md)
- Fields, schema, generator, split → [04_data_card.md](04_data_card.md)
- Detector design, thresholds, intended use → [05_model_card.md](05_model_card.md)
- Privacy/security controls and threat scenarios → [07_privacy_threat_model.md](07_privacy_threat_model.md)

---

# 11. Technical Architecture
## Architecture diagram

```
1. Synthetic FHIR + Claim bundles
        ↓
2. FastAPI ingestion and validation
        ↓
3. Canonical episode and evidence graph
        ↓
4. Rules + similarity + anomaly scoring
        ↓
5. Risk reasons, evidence and uncertainty
        ↓
6. React review workflow
        ↓
7. Human disposition and audit trail
        ↓
8. Offline evaluation and feedback labels
```


## Component rationale
| Component | Technology choice | Why it exists | What is deliberately avoided |
|---|---|---|---|
| Synthetic source | Synthea + deterministic JKN/SATUSEHAT adapter | Privacy-safe, reproducible linked clinical records and injected ground truth | Scraped or invented “real” JKN records |
| Ingestion/API | Python, FastAPI, Pydantic; a documented FHIR R4 subset | Matches team strength; contract-first; schema and reference validation | Full enterprise FHIR server for the prototype |
| Canonical store | PostgreSQL with JSONB for raw resources and relational canonical tables | Preserves source payload while enabling reliable queries and audit | Neo4j or distributed data platform before evidence requires it |
| Evidence graph | In-memory/derived graph using Python/NetworkX; normalized edges persisted | Makes Claim→line→encounter→clinical evidence traceable | GNN as a default model |
| Rules engine | Versioned Python predicates returning reason codes and evidence refs | Deterministic, testable checks for known modes | Hidden thresholds in UI code |
| Similarity | TF-IDF/character n-gram or MinHash baseline; optional multilingual embeddings after baseline | Detects clone-like documentation while preserving a transparent baseline | Vector database unless retrieval scale requires it |
| Anomaly model | Robust peer features + Isolation Forest or Local Outlier Factor baseline | Prioritizes unusual cross-record patterns without pretending to know fraud labels | Deep learning on synthetic labels as headline innovation |
| Risk aggregation | Calibrated rule/signal combiner with reason-level scores | Produces a queue while retaining individual evidence | One uninterpretable probability |
| Frontend | React, TypeScript, accessible component system, ECharts/Recharts; Cytoscape.js only if useful | Operational queue, evidence timeline, comparison, disposition | Decorative AI chat or many inactive menus |
| Audit | Append-only review events in PostgreSQL | Reproducibility, accountability, later label quality | Editing historical decisions in place |
| Evaluation | Python scripts/notebooks producing versioned CSV/JSON/PNG artifacts | Actual evidence for proposal; baseline comparability | Hand-edited result charts |
| Deployment | Docker Compose; local-first demo; optional authorized cloud later | Stable, network-independent demonstration | Live BPJS/SATUSEHAT connection claims |


## Canonical evidence edges
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
## Minimal API contracts
| Endpoint | Input | Output | Key constraints |
|---|---|---|---|
| POST /v1/bundles | JSON synthetic bundle; optional scenario label for demo only | ingestion ID, validation status, resource counts, errors | Scenario label must never enter detector features |
| POST /v1/bundles/{id}/screen | ingestion ID, engine version | case ID, reason codes, scores/bands, evidence refs, latency | Idempotent for same input hash + version |
| GET /v1/cases | state, reason, priority, date filters | paginated queue summary | Pseudonymous fields only |
| GET /v1/cases/{id} | case ID | claim lines, reasons, graph/timeline, comparisons, counter-evidence, versions | No raw sensitive text in list response |
| POST /v1/cases/{id}/dispositions | action, reason, expected case version | immutable event and new state | Optimistic locking; reason required |
| GET /v1/cases/{id}/audit | case ID | ordered audit events | Authorized role only |
| GET /v1/evaluations/{run_id} | run ID | dataset/model versions, metrics, artifacts | Synthetic label displayed prominently |


## Security and observability by design
- Pseudonymous participant/provider IDs in UI; raw source identifiers never required.
- Role model: analyst, senior reviewer, administrator; prototype may simulate roles but must document production enforcement.
- TLS and encryption at rest are production requirements; local demo stores only synthetic data.
- Logs record request IDs, latency, errors, rule/model/schema versions, and counts—not raw medical text.
- Input size/type limits, JSON depth control, malware-safe file handling, and strict content type.
- No arbitrary code execution or prompt ingestion from uploaded bundles.
- Deterministic input hash makes results reproducible.
- Health checks and seeded demo reset make the live demo reliable.

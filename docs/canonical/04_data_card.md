> Sumber: docs/HEALTHKATHON_2026_WINNING_MASTER_PLAN.docx §09
> Status: canonical — read-only. Perubahan hanya lewat ADR baru.


# 04 — Data Card (Data Strategy)

**Cross-reference (jangan salin isinya ke sini):**

- Canonical store and evidence-edge derivation → [03_architecture.md](03_architecture.md)
- Feature families, detectors, thresholds → [05_model_card.md](05_model_card.md)
- Baselines, metrics, experimental protocol → [06_evaluation_plan.md](06_evaluation_plan.md)
- Source labels [E01]..[E26] → [sources.md](sources.md)

---

# 09. Data Strategy
## Data boundary
The prototype must operate on synthetic data only unless the organizer provides written authorization for another dataset. Public reports and aggregate statistics may support the problem statement; they do not become training records. If the BPJS public sample is approved and accessible, use it only as an optional secondary benchmark according to its terms—not as a deadline dependency.
## Minimum required schema
| Domain | Minimum fields | Purpose |
|---|---|---|
| Claim header | claim_id, pseudonymous participant_id, provider_id, encounter_id, care type, submission timestamp, status, total amount, currency | Episode linkage, duplication, queue display |
| Claim lines | line_id, service/product code, description, quantity, unit price, line amount, service timestamp, supporting reference(s) | Evidence match and billing checks |
| Encounter | encounter_id, class, status, start/end, provider, location, participant token | Episode boundary, overlap, chronology |
| Clinical conditions | code system/code, recorded/onset time, verification status, encounter reference | Context only; not used to decide medical necessity in MVP |
| Procedures | code, status, performed time, performer/location, encounter reference | Support billed procedures and detect timing conflicts |
| Medication | request/dispense code, status, quantity, time, encounter reference | Support billed medication lines if available |
| Diagnostics | ServiceRequest, Observation/DiagnosticReport code, status, effective/result time, encounter reference | Support test-related evidence without interpreting clinical values |
| Documents | Composition or note hash/text, author, timestamp, encounter reference | Clone/similarity detection and provenance |
| Billing resources | Account, ChargeItem, Invoice references and totals | Claim-line reconciliation |
| Provenance | resource ID, source type, last-updated, bundle hash/signature placeholder, schema version | Traceability and tamper-aware audit |
| Review | risk type, score/band, reason codes, evidence refs, reviewer disposition/reason/time | Human loop and evaluation labels |


The field names above are the prototype’s internal canonical model. They must map to published SATUSEHAT FHIR resources rather than claiming to reproduce a complete production implementation. [E02–E04]
## Optional enrichment
- Provider peer group, ownership, class, region, and service capability—only from authorized or official sources.
- Referral and ServiceRequest links.
- Case-mix or tariff group code if legally/licensably available.
- Code-system hierarchy and synonyms for comparison.
- Historical reviewer dispositions for later supervised calibration.
- Facility calendar and operational context.
## Candidate public sources and limitations
| Source | Potential use | Access/license status | Limitation for this prototype |
|---|---|---|---|
| SATUSEHAT interoperability documentation [E02–E04] | Schema, resource relationships, flow | Public documentation; respect site terms | Schema—not records, labels, or live API access |
| BPJS public data portal / 2025 sample [E09] | Aggregate or claims-feature research if approved | Registration/proposal/integrity process; exact license must be confirmed | May lack RME bundle, verified risk labels, or selected evidence fields |
| DJSN monthly report [E06] | Scale and financial-context evidence | Public report | Aggregate only; cannot train or establish fraud impact |
| Synthea [E11] | Base synthetic FHIR records | Apache License 2.0 | US-modeled; not representative of Indonesia/JKN |
| BPS aggregate demographics, if used | Parameter ranges for synthetic demographics | Confirm dataset-specific terms | Aggregate localization does not make clinical pathways representative |
| Official code/reference systems | Validation/display | License varies; confirm before redistribution | Some coding/tariff references may be restricted or context-dependent |


## What cannot currently be obtained publicly
Evidence is not established for public availability of:
- real signed JKN Claim + RME Bundles with complete clinical resources;
- verified case-level fraud/waste/abuse labels and reviewer outcomes;
- current BPJS rule thresholds, model features, or operational queue data;
- hospital casemix reviewer timing and false-positive costs;
- production E-Klaim/V-Klaim/SATUSEHAT sandbox credentials;
- authoritative crosswalks for every billing line and supporting clinical event;
- representative narrative notes for cloning detection.
These gaps define the synthetic plan and the later pilot questions; they must not be hidden by confident prose.
## Real public evidence versus synthetic prototype data
| REAL PUBLIC EVIDENCE | SYNTHETIC PROTOTYPE DATA |
|---|---|
| Official categories and rules | Patient, provider, encounter, claim, and evidence records |
| National policy and SATUSEHAT flow/schema | JKN-like canonical mapping and illustrative Rupiah amounts |
| JKN aggregate scale and financial context | Injected phantom, repeat, clone, and unbundling labels |
| Peer-reviewed method limitations | Offline model metrics, timing, and case studies |


No chart may mix these two columns without explicit labeling.
## Synthetic data plan
### Generator
Use Synthea to generate privacy-safe FHIR records, then run a deterministic adapter that:
- pseudonymizes all IDs again for the demo namespace;
- selects a documented subset of FHIR resources;
- constructs synthetic Account/ChargeItem/Invoice/Claim relationships;
- creates internally consistent, illustrative billing amounts;
- injects labeled risk patterns after the clean episode is built;
- writes a machine-readable manifest with random seed, adapter version, injection type, and expected evidence.
Synthea is Apache 2.0 and produces synthetic—not real—patient records. [E11] Its epidemiology, care pathways, and billing assumptions are not representative of JKN. The adapter must never claim otherwise.
### Prototype scale
- Minimum Gate 3: 1,000 claims, at least 300 participants, 8 providers, and 200 injected cases.
- Target evaluation set: 10,000 claims, at least 3,000 participants, 12–20 providers, with 1,200 injected risk cases.
- Inject approximately 300 cases of each selected mode; allow a small, documented multi-label set.
- Include five curated gold demo fixtures separate from statistical evaluation.
The injected prevalence is a test-design choice and must not be described as JKN prevalence.
### Normal patterns
- Every billed procedure has one completed Procedure with compatible encounter and time.
- Claim totals equal the sum of line amounts within rounding tolerance.
- Evidence events occur within plausible encounter windows.
- Each claim belongs to one episode unless a documented follow-up relationship exists.
- Notes and service sequences vary across encounters.
### Injected patterns
| Risk label | Synthetic mutation | Expected evidence shown |
|---|---|---|
| PHANTOM_OR_NO_PROCEDURE_EVIDENCE | Add a billed procedure or drug line without a completed matching Procedure/Dispense event; or mark evidence as entered-in-error | Unsupported line, absent/invalid supporting reference, expected resource type |
| REPEAT_BILLING | Create a second claim for the same participant/provider/episode with overlapping lines; change IDs and small non-material fields | Candidate pair, overlap window, matching lines/amounts, differing fields |
| CLONED_DOCUMENTATION | Copy or lightly alter narrative/service sequence across different participants or encounters | Similarity score, matched fragments or n-gram features, distinct record IDs |
| UNBUNDLING_FRAGMENTATION | Split a coherent episode’s services into temporally adjacent claims or billable groups | Episode timeline, shared context, split amounts, linking signals |


### Labels
Labels are injection-ground-truth labels, not fraud labels. Store:
- injection_id, type, source clean record, target record(s), injector version, random seed;
- expected violated invariants and evidence references;
- difficulty level: obvious, moderate, subtle;
- multi-label status;
- a flag that excludes injector-only metadata from model features.
### Train/validation/test split
- 60% train, 20% validation, 20% test.
- Split first by participant and provider-time block so related records cannot cross partitions.
- Fit unsupervised detectors primarily on clean training records; use validation injections only for threshold selection.
- Freeze the test set before tuning.
- Keep the five demo fixtures outside all metric calculation.
- Report results per mode and macro averages with bootstrap confidence intervals if time permits.
### Leakage controls
- Remove injection manifests, sequential injected IDs, and mutation timestamps from feature tables.
- Regenerate normal identifiers and serialization order after injection.
- Test a trivial classifier against IDs/order; near-perfect performance is a leakage alarm.
- Avoid random row split; use grouped temporal splits.
- Inspect feature importance and manually review false positives/negatives.
### Bias and limitations
- Synthea is US-oriented and may encode non-Indonesian disease, service, and pathway distributions.
- Synthetic providers lack real regional capacity, referral patterns, tariffs, coding practice, and resource scarcity.
- Injected anomalies are simpler than adaptive real-world behavior.
- Document similarity may reflect templating that is legitimate, not cloning.
- Absence of evidence in an incomplete RME is not evidence that a service was not delivered.
- The prototype cannot estimate real-world false-positive cost, savings, or fairness across facilities.
## Data card acceptance criteria
Before evaluation, docs/04_data_card.md must state source, license/terms, generation version, schema, population, injection logic, split logic, missingness, known biases, prohibited uses, and the sentence: “This dataset is synthetic and does not represent JKN prevalence or real provider behavior.”

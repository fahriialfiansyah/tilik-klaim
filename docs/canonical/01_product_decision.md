> Sumber: docs/HEALTHKATHON_2026_WINNING_MASTER_PLAN.docx §00 + §07 + §13
> Status: canonical — read-only. Perubahan hanya lewat ADR baru.


# 01 — Product Decision (Selected Solution, Scope Tiers, Kill Criteria)

**Cross-reference (jangan salin isinya ke sini):**

- Official rules, categories, and submission constraints → [00_competition_brief.md](00_competition_brief.md)
- Assumptions (§07 “Assumptions” lives there) & validation questions → [02_domain_assumptions.md](02_domain_assumptions.md)
- Fields / generator / split → [04_data_card.md](04_data_card.md)
- Thresholds / intended use / prohibited use → [05_model_card.md](05_model_card.md)
- Risks with owners and triggers → [10_risk_register.md](10_risk_register.md)

---

# 00. Executive Summary
## Recommendation
Select Efisiensi Risiko pada Fasilitas Kesehatan and build TilikKlaim as a functional prototype, not a claimed production MVP. The official proposal guide defines a prototype as a limited but functioning and demonstrable implementation; an MVP implies usability by real users. With no current access to hospital or BPJS users, the honest maturity label is functional prototype with a pilot-ready validation plan. [PDF-PP p. 10]
The strategic wedge is narrow: pre-submission integrity screening of the claim evidence bundle. The prototype does not attempt to solve every claim risk, diagnose patients, replace coders, or integrate live BPJS systems. It proves an evidence architecture and four observable patterns using reproducible synthetic data.
## Decision rationale
This direction wins the intersection test better than the alternatives:
- Official problem fit: the target modes are named in the facility category. [PDF-PG pp. 6–7]
- Policy timing: the July 2026 joint circular makes RME-to-claim traceability an immediate national operating direction, not a speculative future. [E01]
- Interoperability feasibility: SATUSEHAT publicly documents the claim flow and the relevant FHIR resources, including Claim, ClaimResponse, Account, ChargeItem, Invoice, Coverage, PurificationDecision, and clinical RME resources. [E02–E04]
- Scale and urgency: the November 2025 DJSN monitoring report recorded 283 million registered participants, 664.3 million visits through November, Rp172.59 trillion in health benefits, and a 108.04% claim ratio; these show operating scale and financial pressure, not fraud prevalence or fraud loss. [E06]
- Buildability: the team can generate synthetic FHIR, implement transparent rules/similarity/anomaly methods, and ship a credible web review loop before 19 September.
- Governance: the system supports rather than replaces human decisions, matching the proposal guide. [PDF-PP pp. 3, 13]
## Explicit non-claims
National JKN fraud prevalence or current fraud loss: Evidence not established. Detailed capability and performance of BPJS internal fraud systems: Evidence not established. Real-world accuracy or savings for TilikKlaim: Evidence not established until an authorized pilot. Detailed functional overlap with 2025 PRO-CLAIM: Evidence not established from public sources.
## Winning narrative in one paragraph
JKN is moving toward claims supported by traceable SATUSEHAT-integrated electronic records. That creates a near-term opportunity: before a claim is submitted, convert its clinical and billing resources into a small evidence graph, test whether each billed event has consistent support, rank anomalous patterns, and let a trained person decide. TilikKlaim makes claim risk visible, reviewable, and auditable. It uses rules where the evidence is deterministic, statistical methods where comparison matters, and no LLM in the risk decision. Its prototype is honest—synthetic, reproducible, measured against a baseline, and designed for authorized integration later.

---

# 07. Selected Solution
## Selection
| Decision item | Selected answer |
|---|---|
| Official category | Efisiensi Risiko pada Fasilitas Kesehatan |
| Prototype modes | cloning; phantom billing / procedure billed but not evidenced; repeat billing; unbundling / fragmentation |
| Primary user | Hospital casemix / anti-fraud officer conducting pre-submission review |
| Secondary future user | BPJS claim verifier using the same evidence package before payment/purification |
| Product maturity | Functional prototype with pilot-ready plan—not a production MVP |


## One-sentence problem statement
Hospital claim teams lack a fast, traceable way to verify that each billed JKN claim line is supported by consistent electronic clinical evidence and to prioritize cross-record anomalies before submission.
## Evidence-backed urgency
The problem is urgent because national policy is explicitly moving JKN claim management toward SATUSEHAT-integrated RME and electronic supporting evidence, while JKN operates at hundreds of millions of visits and significant financial pressure. [E01, E06] This establishes scale and timing, not national fraud loss.
## Proposed solution
TilikKlaim ingests a synthetic SATUSEHAT-shaped Claim/RME bundle, validates its structure, builds evidence links, applies versioned integrity rules, computes similarity/anomaly signals, and produces a ranked review case. The detail screen shows exactly which resource, timestamp, line item, or comparison caused the signal. A human can confirm anomaly, reject the signal, request missing evidence, or escalate; the action and model/rule version are recorded.
## Core innovation
The core innovation is not a new classifier. It is a claim evidence integrity layer that combines:
- standards-shaped clinical and billing provenance;
- deterministic evidence tests for known modes;
- cross-claim similarity and anomaly prioritization;
- counter-evidence and uncertainty on the same screen;
- an auditable human disposition that can later create trustworthy labels.
## Why now, why JKN, why this team
- Why now: the July 2026 joint circular and current SATUSEHAT claim documentation create a timely standards anchor. [E01–E04]
- Why JKN: the official challenge names these modes, and JKN’s volume makes prioritization operationally valuable. [PDF-PG; E06]
- Why this team: Member 1 can build the hybrid engine and API; Member 2 can turn evidence into a usable workflow and reproducible fixtures; Member 3 can control domain claims, governance, and the proposal evidence chain.
## Webinar alignment
Strong: Hospital Modernization; National Data Integration. Moderate: responsible AI Adoption, but not diagnostics. Not forced: Primary-care Enablement.
## Technical advantage versus common approaches
| Common approach | Limitation | TilikKlaim response |
|---|---|---|
| Static rule flags | Brittle and hard to prioritize | Rules remain explicit; similarity/anomaly signals rank uncertain cases |
| Opaque fraud score | Weak investigation value and high accusation risk | Every reason points to source evidence and counter-evidence |
| Generic LLM copilot | Plausible language can exceed evidence | LLM excluded from score; optional summaries are constrained to structured facts |
| Dashboard of aggregates | Shows patterns but not the claim-level proof | Queue opens into a claim-line evidence graph and reviewer action |
| Fully automated rejection | Unsafe and contrary to official human-support framing | Human-only final disposition; no automatic denial, sanction, or code change |


## Main risks
Prior-solution overlap; missing real fields; synthetic bias and leakage; inaccurate mode definitions; insufficient differentiation; and an interface that shows data without guiding action. Section 23 contains triggers and owners. → [10_risk_register.md](10_risk_register.md)
## Backup solution: RujukTepat
Category: Facility. Modes: improper referral and self-referral. Concept: a SATUSEHAT-shaped referral evidence checker that highlights missing clinical/referral evidence, capability mismatch, and network conflicts, then routes the case to human review. It aligns strongly with Primary-care Enablement and National Data Integration, but must avoid medical-necessity decisions without validated pathways.
## Kill criteria and switch rule
Switch to RujukTepat only if a critical feasibility assumption fails—do not switch because a new idea sounds exciting.
| Kill criterion | Deadline | Evidence of failure | Action |
|---|---|---|---|
| Published fields cannot support at least three selected modes | 2 Sep, 18:00 | Schema-to-modus matrix lacks a deterministic or comparison-based observable test for three modes | Stop F1; activate RujukTepat’s missing/contradictory referral evidence scope |
| Synthetic generator cannot create reproducible, linked claims and labels | 2 Sep, 18:00 | Fewer than 1,000 claims, broken linkage, or labels depend on hidden injector artifacts | Fix for four hours; if still blocked, switch |
| Core engine cannot return reason + evidence references for three seeded cases | 5 Sep, 18:00 | Only a score/dashboard exists, or evidence cannot be traced to resources | Switch or narrow to RekonMed if medication linking works |
| Judges cannot distinguish the concept from a generic claim copilot | 6 Sep, 12:00 | Three independent non-domain readers describe it only as “AI fraud detector/chatbot” after a 30-second pitch | Rewrite and redesign once; if still failing, switch |
| Hybrid adds no measurable value over rules-only | 12 Sep, 12:00 | No gain in precision-at-review-budget, recall, or false-positive control on held-out injections | Keep TilikKlaim but remove ML; this is not a product kill |

---

# 13. MVP Scope
## Correct maturity label
Call the submission artifact a functional prototype. Upgrade the label to MVP only after at least one authorized target user can complete the core task with representative data and the team has addressed that feedback. [PDF-PP p. 10]
## Vertical-slice proof
The smallest winning slice is:
| Select or upload a synthetic bundle → screen it → open one flagged reason → inspect claim-to-evidence links → make a human disposition → see the immutable audit event. |
|---|


## Scope tiers
| MUST HAVE | SHOULD HAVE | NICE TO HAVE | OUT OF SCOPE |
|---|---|---|---|
| Published-subset bundle validation | Clone similarity beyond simple baseline | Guarded LLM summary | Real JKN participant data |
| Three modes working by Gate 4; four by Gate 6 | Side-by-side candidate comparison | Scenario builder | Live BPJS/E-Klaim/SATUSEHAT connection |
| Queue with reason and priority | Export a case/evaluation summary | What-if threshold control | Automatic claim rejection/payment/sanction |
| Detail with evidence, counter-evidence, timeline | Review-budget visualization | Advanced graph navigation | Medical-necessity or diagnostic decision |
| Human disposition with required reason | Basic role simulation | Dark mode | Mobile patient app |
| Append-only audit event | Offline evaluation snapshot | Notification integrations | Enterprise IAM, streaming, GNN, multi-agent system |
| Reproducible synthetic evaluation | Error/empty/loading states |  | Many dashboards or dummy menus |


## Pages and core components
- Review Queue / Home — filters for state, reason, and priority; compact operational metrics; case rows with reason, amount, age, and evidence completeness.
- Case Detail — claim lines, reason cards, evidence trace, counter-evidence, episode timeline, side-by-side comparison where relevant, human action panel.
- Ingest / Demo Cases — upload JSON or select seeded case; validation report; run screen; no domain configuration wizard.
- Audit & Evaluation — case audit tab plus one small evaluation page for dataset/model version and synthetic metrics. These may be tabs rather than global navigation items.
## Main dashboard principles
The queue is the dashboard. Limit top metrics to what changes a reviewer’s action:
- cases awaiting review;
- high-priority deterministic conflicts;
- evidence-requested cases;
- median time in queue;
- current engine/dataset version.
Do not show “fraud saved,” provider league tables, or national projections.

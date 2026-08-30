> Sumber: docs/HEALTHKATHON_2026_WINNING_MASTER_PLAN.docx §22
> Status: canonical — read-only. Perubahan hanya lewat ADR baru.


# 08 — Demo Runbook

**Cross-reference (jangan salin isinya ke sini):**

- Scope tiers that define what is demonstrable → [01_product_decision.md](01_product_decision.md)
- Seeded/gold demo fixtures and their exclusion from metrics → [04_data_card.md](04_data_card.md)
- Metrics shown during the measurement beat → [06_evaluation_plan.md](06_evaluation_plan.md)
- Technical demo failure risk and owner → [10_risk_register.md](10_risk_register.md)

---

# 22. Demo Plan
## Ideal demo case
A synthetic inpatient claim includes a billed procedure line, but the bundle has no matching completed Procedure. The bundle is otherwise plausible, and the interface explicitly notes that incomplete evidence is a possible explanation. This gives a clear reason, a safe uncertainty lesson, and an appropriate action: request evidence or escalate—never “fraud confirmed.”
## 90-second flow
| Time | Action | Expected output / narration |
|---|---|---|
| 0–10s | Open queue | “TilikKlaim prioritizes claim evidence risk before submission.” |
| 10–25s | Select top case | Reason says billed procedure lacks completed support; synthetic badge visible |
| 25–50s | Open evidence path | Show claim line → expected Procedure → observed missing/invalid evidence; timeline and counter-evidence |
| 50–70s | Choose Request Evidence | Structured reason prefilled; reviewer edits and confirms |
| 70–82s | Open audit event | Actor, action, evidence, input hash, rule version, time |
| 82–90s | Close | “AI prioritizes; humans decide; every decision is traceable.” |


## Three-minute flow
- 0:00–0:25 — context: one sentence on official facility modes and July 2026 claim/RME integration.
- 0:25–0:45 — input: choose the seeded phantom case; show resource validation and synthetic label.
- 0:45–1:30 — detection/evidence: queue, reason, claim line, evidence path, timeline, incomplete-bundle caveat.
- 1:30–2:00 — human action: request evidence, enter reason, see state change and audit.
- 2:00–2:25 — contrast case: open a clone similarity false positive caused by legitimate templating; dismiss it with counter-evidence.
- 2:25–2:45 — measurement: show rules-only vs hybrid on frozen synthetic data and false positives/100.
- 2:45–3:00 — close: standards-compatible pilot path; no live integration or real-data claim.
## Expected user actions and outputs
| User action | System output |
|---|---|
| Upload/select bundle | Validation, resource count, input hash, errors |
| Screen | Reasons, priority band, component scores, latency, engine version |
| Select reason | Evidence/counter-evidence refs, timeline, comparison if relevant |
| Disposition | New state and append-only event |
| View evaluation | Dataset/model versions, baseline metrics, limitations |


## Demo reliability
- Use deterministic seeded fixtures and local Docker Compose.
- Warm the application and cache; then reset to a known state.
- Test on the presentation machine, offline.
- Keep one-click scripts for start, health check, seed, and reset.
- Record screen at 1080p with the same narration and cursor path.
- Export a six-frame screenshot PDF as a last fallback.
- Never depend on a remote LLM, SATUSEHAT, BPJS, or cloud database.
## Fallback if live demo fails
Say one sentence—“The local service did not start; here is the identical deterministic run captured from release <hash>”—then play the 90-second recording. Do not troubleshoot on stage. Keep screenshots ready if video playback also fails.

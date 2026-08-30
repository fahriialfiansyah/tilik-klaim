# Task 02 — Versioned rule engine for three risk modes

**Stack:** backend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** ✅ Done
**Foundation:** no
**Autonomous:** yes
**Depends on:**
- [`./01-evidence-graph.md`](./01-evidence-graph.md) — rules run over derived edges

## Goal

Emit versioned reason codes with resolvable evidence and counter-evidence for phantom,
repeat, and unbundling — with clone as a baseline if time allows.

## Files to touch

- `apps/backend/app/service/rules/phantom.py`
- `apps/backend/app/service/rules/repeat.py`
- `apps/backend/app/service/rules/unbundling.py`
- `apps/backend/app/service/rules/clone_baseline.py` — optional at this gate
- `apps/backend/app/service/rules/registry.py` — versioned rule interface
- `apps/backend/app/service/screening.py` — `POST /v1/bundles/{id}/screen`
- `apps/backend/tests/test_rules_gold.py`

## Skills to consult

- `docs/canonical/05_model_card.md` § Detector design by mode — required explanation per mode
- `docs/canonical/05_model_card.md` § Risk aggregation — the caps and gates

## TODOs

- [x] Versioned rule interface returning reason code + evidence refs + counter-evidence
- [x] Phantom rule: billed line with no completed matching event; surface expected evidence type and resources searched
- [x] Repeat rule: claim/episode fingerprint and overlap; surface the candidate pair, matched and differing fields
- [x] Unbundling rule: same participant/provider, adjacent time, shared episode; surface the timeline and split amounts
- [x] Clone baseline (delivered, not deferred): character n-gram or MinHash similarity above a validated threshold
- [x] **Counter-evidence is returned alongside every reason**, not as a separate lookup
- [x] Priority bands: deterministic conflict · high-priority signal · needs context · no observed risk
- [x] **Cap:** text similarity alone can never reach the highest band
- [x] **Cap:** missing evidence + incomplete bundle *lowers* certainty and routes to request-evidence
- [x] **Cap:** exact duplicate fingerprint is high priority but still human-reviewed
- [x] Store all component scores and versions, not just the aggregate
- [x] "No observed risk" never renders as "clean" or "safe"
- [x] No hardcoded "75% = fraud" threshold; bands are calibrated and their basis is exposed
- [x] **Test — unit per predicate:** each rule fires on its gold fixture
- [x] **Test — counterexample:** the clean fixture produces no injected reason
- [x] **Test — integration, history lookup:** repeat detection finds the prior claim
- [x] **Test — snapshot response:** the screen response shape stays stable
- [x] **Edge case — incomplete bundle:** band lowered, request-evidence suggested
- [x] **Edge case — entered-in-error status:** treated as absent evidence, with that reason stated
- [x] **Edge case — overlapping legitimate follow-up:** surfaces as counter-evidence, not suppressed
- [x] **Edge case — rounding:** amount reconciliation uses the documented tolerance
- [x] **Edge case — multiple candidates:** all candidate pairs returned, ranked

## Done when

Three modes pass their gold-fixture tests; the clean fixture produces no injected reason;
every evidence reference resolves; screening the same hash at the same version is
deterministic; and the reason catalog is documented and integrated into the API.

## Closing checklist

- [x] All `## TODOs` items above are `[x]`
- [x] Done-when assertion verified
- [x] Top-of-file header literally reads `**Status:** ✅ Done`
- [x] Changelog entry appended to `changelog/backend.md`

## Notes

Medical-necessity rules are **out of scope**. The rules here test structural evidence only.
Inventing clinical rules without a domain expert is the fastest way to produce confident,
wrong output — and it is listed as a named risk in `docs/canonical/10_risk_register.md`.

## Notes

**The fingerprint includes the encounter, and that carries the whole distinction between this
rule's two reasons.** Without it the repeat fixture screened to `DUPLICATE_CLAIM_FINGERPRINT`
instead of `OVERLAPPING_CLAIM_SAME_EPISODE`. The same service at a *different visit* is ordinary
repeat care, not a duplicate submission — only the weaker reason lets a reviewer see the timing
and the differing fields before judging.

**Every missing-evidence reason carries an unconditional counter-note.** The first draft
attached incompleteness caveats only when the bundle was actually incomplete, which left the
most accusatory reason in the system shipping with no argument against it whenever the bundle
was complete. A bundle only ever shows what was *sent*; evidence may sit on paper or in another
system. That caveat is not conditional, so neither is the note. A test now enforces it.

**Two floors, two different jobs.** `SIMILARITY_CANDIDATE_FLOOR` (graph, 0.5) decides whether a
pair is worth linking; `REPORTING_THRESHOLD` (clone rule, 0.7) decides whether to raise a reason
at all. Both are exposed as component scores rather than buried, both are provisional pending
Sprint 06 calibration, and neither can drive the top band — the similarity cap forbids it.

Clone baseline was delivered rather than deferred, so all four risk modes screen at this gate
instead of the three the gate required.

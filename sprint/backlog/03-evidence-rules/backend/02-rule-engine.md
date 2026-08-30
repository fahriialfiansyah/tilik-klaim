# Task 02 — Versioned rule engine for three risk modes

**Stack:** backend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** 📋 Planned
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

- [ ] Versioned rule interface returning reason code + evidence refs + counter-evidence
- [ ] Phantom rule: billed line with no completed matching event; surface expected evidence type and resources searched
- [ ] Repeat rule: claim/episode fingerprint and overlap; surface the candidate pair, matched and differing fields
- [ ] Unbundling rule: same participant/provider, adjacent time, shared episode; surface the timeline and split amounts
- [ ] Clone baseline (if time allows): character n-gram or MinHash similarity above a validated threshold
- [ ] **Counter-evidence is returned alongside every reason**, not as a separate lookup
- [ ] Priority bands: deterministic conflict · high-priority signal · needs context · no observed risk
- [ ] **Cap:** text similarity alone can never reach the highest band
- [ ] **Cap:** missing evidence + incomplete bundle *lowers* certainty and routes to request-evidence
- [ ] **Cap:** exact duplicate fingerprint is high priority but still human-reviewed
- [ ] Store all component scores and versions, not just the aggregate
- [ ] "No observed risk" never renders as "clean" or "safe"
- [ ] No hardcoded "75% = fraud" threshold; bands are calibrated and their basis is exposed
- [ ] **Test — unit per predicate:** each rule fires on its gold fixture
- [ ] **Test — counterexample:** the clean fixture produces no injected reason
- [ ] **Test — integration, history lookup:** repeat detection finds the prior claim
- [ ] **Test — snapshot response:** the screen response shape stays stable
- [ ] **Edge case — incomplete bundle:** band lowered, request-evidence suggested
- [ ] **Edge case — entered-in-error status:** treated as absent evidence, with that reason stated
- [ ] **Edge case — overlapping legitimate follow-up:** surfaces as counter-evidence, not suppressed
- [ ] **Edge case — rounding:** amount reconciliation uses the documented tolerance
- [ ] **Edge case — multiple candidates:** all candidate pairs returned, ranked

## Done when

Three modes pass their gold-fixture tests; the clean fixture produces no injected reason;
every evidence reference resolves; screening the same hash at the same version is
deterministic; and the reason catalog is documented and integrated into the API.

## Closing checklist

- [ ] All `## TODOs` items above are `[x]`
- [ ] Done-when assertion verified
- [ ] Top-of-file header literally reads `**Status:** ✅ Done`
- [ ] Changelog entry appended to `changelog/backend.md`

## Notes

Medical-necessity rules are **out of scope**. The rules here test structural evidence only.
Inventing clinical rules without a domain expert is the fastest way to produce confident,
wrong output — and it is listed as a named risk in `docs/canonical/10_risk_register.md`.

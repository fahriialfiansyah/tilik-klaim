"""The rule engine, checked against the gold fixtures and the model card's caps.

The caps get more attention here than the detectors do. A detector that misses a case costs a
review; a cap that fails lets the system overstate what it knows about a person or a facility.
"""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from tilik_domain.canonical import EventStatus, ResourceRef, ResourceType
from tilik_domain.reasons import (
    DispositionAction,
    PriorityBand,
    ReasonCode,
    RiskMode,
)

from app.service.evidence_graph import build_evidence_graph
from app.service.rules.clone_baseline import REPORTING_THRESHOLD, CloneBaselineRule
from app.service.rules.phantom import PhantomRule
from app.service.rules.registry import RuleContext, RuleRegistry
from app.service.rules.repeat import ROUNDING_TOLERANCE, RepeatBillingRule
from app.service.rules.unbundling import UnbundlingRule
from app.service.screening import (
    DEFAULT_REGISTRY,
    Certainty,
    ScreeningResult,
    input_hash,
    screen_bundle,
)
from tests.fixtures import SCENARIOS, load


def screen(scenario: str) -> ScreeningResult:
    fixture = load(scenario)
    return screen_bundle(fixture.bundle, fixture.history)


# --------------------------------------------------------------------------------------
# Unit per predicate — each rule fires on the fixture that exists to prove it
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("scenario", "rule", "expected_mode"),
    [
        ("phantom", PhantomRule(), RiskMode.PHANTOM_OR_NO_PROCEDURE_EVIDENCE),
        ("repeat", RepeatBillingRule(), RiskMode.REPEAT_BILLING),
        ("unbundled", UnbundlingRule(), RiskMode.UNBUNDLING_FRAGMENTATION),
        ("clone", CloneBaselineRule(), RiskMode.CLONED_DOCUMENTATION),
    ],
)
def test_each_rule_fires_on_its_own_fixture(scenario, rule, expected_mode) -> None:
    fixture = load(scenario)
    graph = build_evidence_graph(fixture.bundle, history=fixture.history)
    hits = rule.evaluate(
        RuleContext(bundle=fixture.bundle, history=fixture.history, graph=graph)
    )
    assert hits, f"{rule.rule_id} produced nothing on its own scenario"
    assert all(hit.mode is expected_mode for hit in hits)


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_screening_emits_exactly_the_expected_reason_codes(scenario: str) -> None:
    """The fixture answer key is the contract. Extra reasons are false positives."""
    fixture = load(scenario)
    result = screen(scenario)
    assert {hit.code for hit in result.reasons} == set(fixture.expected_reason_codes)


# --------------------------------------------------------------------------------------
# Counterexample — the clean fixture must stay silent, and must not be called clean
# --------------------------------------------------------------------------------------


def test_clean_fixture_produces_no_reason() -> None:
    result = screen("clean")
    assert result.reasons == ()
    assert result.band is PriorityBand.NO_OBSERVED_RISK
    assert result.suggested_action is None


def test_no_observed_risk_is_not_a_claim_of_safety() -> None:
    """The band name is the only wording available, and it must not say clean or safe."""
    result = screen("clean")
    assert not result.has_observed_risk
    band = str(result.band).lower()
    for forbidden in ("clean", "safe", "clear", "ok", "valid"):
        assert forbidden not in band


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_no_rule_ever_uses_the_word_fraud(scenario: str) -> None:
    for hit in screen(scenario).reasons:
        text = " ".join([hit.sentence_id, *(c.note_id for c in hit.counter_evidence)]).lower()
        for forbidden in ("fraud", "curang", "palsu", "tolak", "sanksi"):
            assert forbidden not in text, f"{hit.code} says {forbidden!r}"


# --------------------------------------------------------------------------------------
# Evidence and counter-evidence travel together
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_every_reason_carries_resolvable_evidence(scenario: str) -> None:
    fixture = load(scenario)
    known = set()
    for bundle in (*fixture.history, fixture.bundle):
        known |= set(bundle.resource_index())

    for hit in screen(scenario).reasons:
        assert hit.evidence, f"{hit.code} has no evidence to open"
        for ref in hit.evidence:
            if not ref.resource_type.is_stored_resource:
                continue
            assert ref.key() in known, f"{hit.code} points at absent {ref.resource_id}"


def test_counter_evidence_is_returned_with_the_reason_not_separately() -> None:
    """A reviewer who only sees the case *for* a signal cannot weigh it."""
    for scenario in ("phantom", "repeat", "unbundled", "clone"):
        for hit in screen(scenario).reasons:
            assert hit.counter_evidence, (
                f"{scenario}/{hit.code} offers no argument against itself"
            )


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_component_scores_are_stored_not_just_an_aggregate(scenario: str) -> None:
    for hit in screen(scenario).reasons:
        assert hit.component_scores, f"{hit.code} kept no component scores"
        assert hit.rule_id and hit.ruleset_version


# --------------------------------------------------------------------------------------
# The three caps from the model card
# --------------------------------------------------------------------------------------


def test_cap_text_similarity_alone_never_reaches_the_top_band() -> None:
    """Shared templates are ordinary practice, so similarity alone cannot top the queue."""
    result = screen("clone")
    assert {hit.code for hit in result.reasons} == {ReasonCode.NEAR_DUPLICATE_DOCUMENTATION}
    assert result.band is PriorityBand.NEEDS_CONTEXT
    assert result.band is not PriorityBand.DETERMINISTIC_CONFLICT
    assert result.band is not PriorityBand.HIGH_PRIORITY_SIGNAL


def test_cap_incomplete_bundle_lowers_the_band_and_asks_for_evidence() -> None:
    """Missing evidence plus an incomplete bundle must not climb toward confirm-anomaly."""
    fixture = load("phantom")
    baseline = screen_bundle(fixture.bundle, fixture.history)
    assert baseline.band is PriorityBand.DETERMINISTIC_CONFLICT
    assert baseline.certainty is Certainty.FULL

    dangling = ResourceRef(resource_type=ResourceType.PROCEDURE, resource_id="PROC-GONE")
    lines = (
        fixture.bundle.lines[0].model_copy(update={"supporting_refs": (dangling,)}),
        *fixture.bundle.lines[1:],
    )
    incomplete = fixture.bundle.model_copy(update={"lines": lines})

    result = screen_bundle(incomplete, fixture.history)

    assert result.certainty is Certainty.REDUCED_INCOMPLETE_BUNDLE
    assert result.band is PriorityBand.HIGH_PRIORITY_SIGNAL, "band must step down"
    assert result.suggested_action is DispositionAction.REQUEST_EVIDENCE
    assert result.suggested_action is not DispositionAction.CONFIRM_ANOMALY


def test_cap_exact_duplicate_is_high_priority_but_still_human_reviewed() -> None:
    """A duplicate fingerprint tops the queue and still decides nothing."""
    fixture = load("repeat")
    twin = fixture.bundle.model_copy(
        update={"claim": fixture.bundle.claim.model_copy(update={"claim_id": "CLM-RP-TWIN"})}
    )
    result = screen_bundle(twin, (fixture.bundle,))

    codes = {hit.code for hit in result.reasons}
    assert ReasonCode.DUPLICATE_CLAIM_FINGERPRINT in codes
    assert result.band is PriorityBand.DETERMINISTIC_CONFLICT
    assert result.suggested_action is not DispositionAction.CONFIRM_ANOMALY


def test_no_hardcoded_fraud_threshold_and_bands_expose_their_basis() -> None:
    """Thresholds must be visible as component scores, not buried as a magic cutoff."""
    hits = screen("clone").reasons
    similarity = next(h for h in hits if h.code is ReasonCode.NEAR_DUPLICATE_DOCUMENTATION)
    assert similarity.score("text_similarity") is not None
    assert similarity.score("reporting_threshold") == REPORTING_THRESHOLD
    assert similarity.score("text_similarity") >= REPORTING_THRESHOLD


# --------------------------------------------------------------------------------------
# Edge cases named by the task
# --------------------------------------------------------------------------------------


def test_entered_in_error_evidence_is_treated_as_absent_and_says_so() -> None:
    fixture = load("phantom")
    retracted = tuple(
        proc.model_copy(update={"status": EventStatus.ENTERED_IN_ERROR})
        for proc in fixture.bundle.procedures
    )
    bundle = fixture.bundle.model_copy(update={"procedures": retracted})

    result = screen_bundle(bundle, fixture.history)
    codes = {hit.code for hit in result.reasons}

    assert ReasonCode.SUPPORTING_EVIDENCE_ENTERED_IN_ERROR in codes
    hit = next(h for h in result.reasons if h.code is ReasonCode.SUPPORTING_EVIDENCE_ENTERED_IN_ERROR)
    assert any("keliru-input" in c.note_id for c in hit.counter_evidence)


def test_a_legitimate_follow_up_surfaces_as_counter_evidence_not_suppression() -> None:
    """The overlap is still reported; the reason simply carries the argument against it."""
    fixture = load("repeat")
    far_apart = fixture.bundle.model_copy(
        update={
            "claim": fixture.bundle.claim.model_copy(
                update={
                    "submitted_at": fixture.bundle.claim.submitted_at + timedelta(days=21)
                }
            )
        }
    )
    result = screen_bundle(far_apart, fixture.history)
    overlap = [h for h in result.reasons if h.code is ReasonCode.OVERLAPPING_CLAIM_SAME_EPISODE]

    assert overlap, "a distant repeat must still be reported, not silently dropped"
    notes = " ".join(c.note_id for c in overlap[0].counter_evidence)
    assert "kunjungan ulang yang sah" in notes


def test_rounding_difference_does_not_become_a_differing_field() -> None:
    """A one-cent gap must not tell a reviewer the two claims bill different sums."""
    fixture = load("repeat")
    nudged_claim = fixture.bundle.claim.model_copy(
        update={"total_amount": fixture.bundle.claim.total_amount + ROUNDING_TOLERANCE}
    )
    nudged = fixture.bundle.model_copy(update={"claim": nudged_claim})

    result = screen_bundle(nudged, fixture.history)
    overlap = [h for h in result.reasons if h.code is ReasonCode.OVERLAPPING_CLAIM_SAME_EPISODE]
    if overlap:
        notes = " ".join(c.note_id for c in overlap[0].counter_evidence)
        assert "total tagihan" not in notes


def test_multiple_candidates_are_all_returned_and_ordered_stably() -> None:
    fixture = load("repeat")
    prior = fixture.history[0]
    second = prior.model_copy(
        update={
            "bundle_id": "BND-RP-C",
            "claim": prior.claim.model_copy(update={"claim_id": "CLM-RP-C"}),
        }
    )
    result = screen_bundle(fixture.bundle, (prior, second))
    targets = [
        ref.resource_id
        for hit in result.reasons
        if hit.mode is RiskMode.REPEAT_BILLING
        for ref in hit.evidence
        if ref.resource_type is ResourceType.CLAIM
    ]
    assert "CLM-RP-A" in targets and "CLM-RP-C" in targets
    assert result.reasons == screen_bundle(fixture.bundle, (second, prior)).reasons


# --------------------------------------------------------------------------------------
# Reproducibility and response shape
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_same_input_hash_and_version_screens_identically(scenario: str) -> None:
    fixture = load(scenario)
    first = screen_bundle(fixture.bundle, fixture.history)
    second = screen_bundle(fixture.bundle, fixture.history)
    assert first.input_hash == second.input_hash
    assert first.model_dump() == second.model_dump()


def test_input_hash_changes_when_the_billed_content_changes() -> None:
    fixture = load("clean")
    line = fixture.bundle.lines[0]
    changed = fixture.bundle.model_copy(
        update={
            "lines": (
                line.model_copy(update={"line_amount": line.line_amount + Decimal("1.00")}),
                *fixture.bundle.lines[1:],
            )
        }
    )
    assert input_hash(fixture.bundle) != input_hash(changed)


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_screening_result_shape_is_stable(scenario: str) -> None:
    """The snapshot the API serialises. Adding a field is fine; losing one breaks the UI."""
    payload = screen(scenario).model_dump(mode="json")
    assert set(payload) == {
        "bundle_id",
        "input_hash",
        "band",
        "certainty",
        "reasons",
        "gaps",
        "suggested_action",
        "identity",
        "rule_ids",
    }
    assert payload["identity"]["ruleset_version"]
    assert payload["rule_ids"] == list(DEFAULT_REGISTRY.rule_ids())


def test_registry_refuses_duplicate_rule_ids() -> None:
    with pytest.raises(ValueError, match="duplicate rule ids"):
        RuleRegistry((PhantomRule(), PhantomRule()))

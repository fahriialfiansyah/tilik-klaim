"""Gold fixtures parse, resolve, and reconcile.

These assertions are the foundation contract: Sprints 02, 03, 04, and 06 all build on the
guarantee that these five bundles are internally consistent.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from tests.fixtures import SCENARIOS, load, load_all
from tilik_domain.canonical import CanonicalBundle
from tilik_domain.reasons import REASON_CATALOG

ROUNDING_TOLERANCE = Decimal("0.01")
"""Claim totals may differ from the sum of lines by at most this much.

Documented rather than hidden inside a float comparison, per WS-001's rounding edge case.
"""


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_fixture_parses_into_canonical_model(scenario: str) -> None:
    fixture = load(scenario)
    assert isinstance(fixture.bundle, CanonicalBundle)
    assert fixture.bundle.lines, "a claim with no billed lines cannot be screened"


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_every_reference_resolves(scenario: str) -> None:
    """A reference pointing at an absent resource is a defect, not an empty display."""
    fixture = load(scenario)
    for bundle in (*fixture.history, fixture.bundle):
        unresolved = bundle.unresolved_refs()
        assert not unresolved, f"{bundle.bundle_id} has dangling refs: {unresolved}"


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_claim_total_reconciles_with_lines(scenario: str) -> None:
    fixture = load(scenario)
    for bundle in (*fixture.history, fixture.bundle):
        line_sum = sum((line.line_amount for line in bundle.lines), Decimal("0"))
        delta = abs(bundle.claim.total_amount - line_sum)
        assert delta <= ROUNDING_TOLERANCE, f"{bundle.bundle_id} off by {delta}"


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_chronology_is_sound(scenario: str) -> None:
    """No procedure precedes the encounter it belongs to, and no claim predates its service."""
    fixture = load(scenario)
    for bundle in (*fixture.history, fixture.bundle):
        encounters = {enc.encounter_id: enc for enc in bundle.encounters}
        for procedure in bundle.procedures:
            encounter = encounters[procedure.encounter_id]
            assert procedure.performed_at >= encounter.start_at, (
                f"{procedure.procedure_id} performed before its encounter started"
            )
        for line in bundle.lines:
            assert bundle.claim.submitted_at >= line.service_at, (
                f"{line.line_id} claimed before the service occurred"
            )


def test_clean_fixture_expects_no_reason() -> None:
    """The counterexample. If the clean case ever produces a reason, the engine is wrong."""
    assert load("clean").expected_reason_codes == ()


@pytest.mark.parametrize("scenario", [s for s in SCENARIOS if s != "clean"])
def test_injected_fixture_expects_a_catalogued_reason(scenario: str) -> None:
    fixture = load(scenario)
    assert fixture.expected_reason_codes, f"{scenario} must expect at least one reason"
    for code in fixture.expected_reason_codes:
        assert code in REASON_CATALOG, f"{code} is not in the reason catalog"


def test_all_four_risk_modes_have_a_fixture() -> None:
    """Gate 4 needs three modes working; Gate 6 needs four. Each needs a fixture to test."""
    covered = {
        REASON_CATALOG[code].mode
        for fixture in load_all()
        for code in fixture.expected_reason_codes
    }
    assert len(covered) == 4, f"only {len(covered)} of 4 risk modes have a gold fixture"


def test_fixtures_carry_no_real_identifiers() -> None:
    """Pseudonymous only — no names, no NIK. Asserted, not merely intended."""
    for fixture in load_all():
        for bundle in (*fixture.history, fixture.bundle):
            assert bundle.claim.participant_id.startswith("PSN-")
            for encounter in bundle.encounters:
                assert encounter.participant_id.startswith("PSN-")

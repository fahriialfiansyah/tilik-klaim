"""Reason catalog invariants."""
from __future__ import annotations

import pytest

from tilik_domain.canonical import ResourceType
from tilik_domain.reasons import (
    ALLOWED_TRANSITIONS,
    REASON_CATALOG,
    CaseState,
    DispositionAction,
    PriorityBand,
    ReasonCode,
    RiskMode,
    codes_for_mode,
    definition_for,
)


def test_every_reason_code_is_catalogued() -> None:
    """A code the UI can receive but cannot explain is a defect."""
    assert set(REASON_CATALOG) == set(ReasonCode)


def test_every_reason_has_a_working_language_sentence() -> None:
    for definition in REASON_CATALOG.values():
        assert definition.sentence_id.strip(), f"{definition.code} has no sentence"
        assert definition.sentence_id.endswith("."), f"{definition.code} sentence is not a sentence"


def test_no_reason_sentence_accuses_anyone() -> None:
    """The system reports risk requiring review; it never states fraud.

    A wording slip here turns a work aid into an accusation tool, which is why this is a test
    and not a style note.
    """
    forbidden = ("fraud", "penipuan", "kecurangan", "melanggar hukum", "terbukti")
    for definition in REASON_CATALOG.values():
        lowered = definition.sentence_id.lower()
        for term in forbidden:
            assert term not in lowered, f"{definition.code} uses accusatory wording: {term!r}"


def test_every_reason_requires_at_least_one_evidence_type() -> None:
    """A reason with no required evidence could be displayed with nothing to check."""
    for definition in REASON_CATALOG.values():
        assert definition.required_evidence, f"{definition.code} requires no evidence"
        for resource_type in definition.required_evidence:
            assert isinstance(resource_type, ResourceType)


def test_every_risk_mode_has_at_least_one_reason() -> None:
    for mode in RiskMode:
        assert codes_for_mode(mode), f"{mode} has no reason code"


def test_clone_reason_is_not_deterministic() -> None:
    """Documentation similarity is inferred, never an outright invariant violation.

    Legitimate template use produces high similarity too, so this reason must stay
    non-deterministic and can never alone reach the top priority band.
    """
    assert definition_for(ReasonCode.NEAR_DUPLICATE_DOCUMENTATION).deterministic is False


def test_unknown_reason_code_raises() -> None:
    with pytest.raises(KeyError):
        definition_for("NOT_A_REAL_CODE")  # type: ignore[arg-type]


def test_state_model_covers_every_state() -> None:
    assert set(ALLOWED_TRANSITIONS) == set(CaseState)


def test_escalated_is_terminal_with_no_automated_action() -> None:
    """Escalation routes to authorized investigation. Nothing follows it automatically."""
    assert ALLOWED_TRANSITIONS[CaseState.ESCALATED] == frozenset()


def test_evidence_requested_returns_to_screened() -> None:
    """A new bundle version re-screens the case rather than closing it."""
    assert CaseState.SCREENED in ALLOWED_TRANSITIONS[CaseState.EVIDENCE_REQUESTED]


def test_dismissed_can_be_reopened() -> None:
    assert CaseState.IN_REVIEW in ALLOWED_TRANSITIONS[CaseState.DISMISSED]


def test_no_observed_risk_band_exists_and_is_not_named_clean() -> None:
    """The system may say no detector fired. It may never say the claim is clean."""
    assert PriorityBand.NO_OBSERVED_RISK.value == "NO_OBSERVED_RISK"
    band_names = " ".join(band.value.lower() for band in PriorityBand)
    assert "clean" not in band_names and "safe" not in band_names


def test_four_disposition_actions_and_none_is_a_verdict() -> None:
    assert len(list(DispositionAction)) == 4
    names = " ".join(action.value.lower() for action in DispositionAction)
    for verdict in ("fraud", "reject_claim", "deny", "sanction"):
        assert verdict not in names

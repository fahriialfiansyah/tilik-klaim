"""Reason catalog invariants."""
from __future__ import annotations

import pytest

from tilik_domain.canonical import ResourceType
from tilik_domain.locale import Locale
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


@pytest.mark.parametrize("locale", list(Locale))
def test_every_reason_has_a_sentence_in_every_language(locale: Locale) -> None:
    """A language we offer but cannot speak for some reason is a half-translated screen."""
    for definition in REASON_CATALOG.values():
        sentence = definition.sentence(locale)
        assert sentence.strip(), f"{definition.code} has no {locale} sentence"
        assert sentence.endswith("."), f"{definition.code} {locale} sentence is not a sentence"


def test_the_two_languages_are_renderings_of_one_catalog() -> None:
    """Same codes, same count, and never the same string twice.

    An English sentence left equal to its Indonesian original is an untranslated entry that
    would otherwise ship silently — the screen would render, just in the wrong language.
    """
    for definition in REASON_CATALOG.values():
        assert definition.sentence_id != definition.sentence_en, (
            f"{definition.code} was never translated"
        )


@pytest.mark.parametrize("locale", list(Locale))
def test_no_reason_sentence_accuses_anyone(locale: Locale) -> None:
    """The system reports risk requiring review; it never states fraud.

    A wording slip here turns a work aid into an accusation tool, which is why this is a test
    and not a style note. English gets its own forbidden terms rather than a translation of the
    Indonesian list: the accusation reads differently in each language.
    """
    forbidden = (
        "fraud",
        "penipuan",
        "kecurangan",
        "melanggar hukum",
        "terbukti",
        "fraudulent",
        "proven",
        "illegal",
    )
    for definition in REASON_CATALOG.values():
        lowered = definition.sentence(locale).lower()
        for term in forbidden:
            assert term not in lowered, f"{definition.code} uses accusatory wording: {term!r}"


def test_english_sentences_describe_the_record_not_the_act() -> None:
    """Absence of a record is not evidence a service was not delivered.

    English makes this failure easy in a way Indonesian does not: "no completed procedure
    record" and "the procedure was not performed" are a short edit apart, and only the first is
    a claim this system is entitled to make.
    """
    forbidden = (
        "was not performed",
        "were not performed",
        "did not happen",
        "never delivered",
        "was not delivered",
        "did not occur",
    )
    for definition in REASON_CATALOG.values():
        lowered = definition.sentence_en.lower()
        for phrase in forbidden:
            assert phrase not in lowered, (
                f"{definition.code} states what someone did, not what the record shows: {phrase!r}"
            )


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


def test_expected_support_names_what_is_missing_not_what_is_cited() -> None:
    """The two evidence fields diverge exactly where a reviewer would be misled otherwise.

    A phantom reason *requires* the line and the visit — without them it could not be stated at
    all — and *expects* a completed procedure that is not there. Reporting the first as
    "expected evidence" told the screen everything had been found, on the one case whose whole
    finding is an absence.
    """
    phantom = definition_for(ReasonCode.LINE_WITHOUT_COMPLETED_PROCEDURE)
    assert ResourceType.PROCEDURE in phantom.expected_support
    assert ResourceType.PROCEDURE not in phantom.required_evidence

    medication = definition_for(ReasonCode.LINE_WITHOUT_MEDICATION_DISPENSE)
    assert ResourceType.MEDICATION in medication.expected_support


def test_every_reason_states_the_support_it_expects() -> None:
    """Defaulting to `required_evidence` keeps the field non-optional for readers."""
    for definition in REASON_CATALOG.values():
        assert definition.expected_support, f"{definition.code} expects nothing"

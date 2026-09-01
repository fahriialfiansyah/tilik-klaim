"""The model card must be complete, and must not quote a metric nobody measured.

`docs/canonical/05_model_card.md` § Model/version artifacts names eight required sections. A
card that quietly loses its limitations section is worse than no card, because it looks like
disclosure. And § 20's constraint is that every metric in the proposal comes from a generated
artifact — so this card states that its metrics are pending and names the sprint that produces
them, rather than carrying a number somebody typed.
"""
from __future__ import annotations

import re

import pytest
from tilik_model.model_card import (
    MANDATORY_SENTENCE,
    METRICS_PENDING_NOTE,
    REQUIRED_ELEMENTS,
    ModelCardInputs,
    missing_elements,
    render,
)
from tilik_model.ranking import RankingModel


@pytest.fixture(scope="module")
def card(bundles) -> str:
    half = len(bundles) // 2
    model = RankingModel.train(
        training_bundles=bundles[:half],
        validation_bundles=bundles[half:],
        dataset_digest="a1b2c3d4e5f6",
    )
    return render(
        ModelCardInputs(
            model=model,
            training_bundles=half,
            validation_bundles=len(bundles) - half,
            dropped_contaminated_bundles=7,
        )
    )


def test_every_required_section_is_present(card) -> None:
    assert missing_elements(card) == ()
    for element in REQUIRED_ELEMENTS:
        assert f"## {element}" in card, element


def test_the_mandatory_sentence_is_present_verbatim(card) -> None:
    """The ethical core, in the artifact itself rather than only in a review conversation."""
    assert MANDATORY_SENTENCE in card


def test_the_card_never_uses_the_word_fraud(card) -> None:
    """The system reports risk or anomaly requiring review. It does not state fraud."""
    assert not re.search(r"\bfraud\b", card, flags=re.IGNORECASE)


def test_the_card_quotes_no_invented_metric(card) -> None:
    """Sprint 06 measures. Until then, a number here would be a number someone made up."""
    assert METRICS_PENDING_NOTE in card
    for invented in ("precision@k of", "recall@k of", "AUC ", "F1 of"):
        assert invented.lower() not in card.lower()


def test_the_card_lists_every_feature_and_its_imputation(card) -> None:
    from tilik_model.feature_schema import FEATURE_SCHEMA

    for spec in FEATURE_SCHEMA:
        assert spec.name in card, spec.name
        assert spec.imputation_note in card, spec.name


def test_the_card_records_the_thresholds_and_hyperparameters(card) -> None:
    """A threshold nobody can find is not a documented threshold."""
    assert "n_estimators" in card
    assert "validation" in card.lower()
    assert "quantile" in card.lower()


def test_the_card_states_the_removal_criterion(card) -> None:
    """Removal is a designed outcome; a card that omits it misrepresents the method."""
    assert "remove" in card.lower()


def test_missing_elements_actually_detects_a_missing_section() -> None:
    """A completeness check that never fires would not be a check."""
    assert "Limitations" in missing_elements("# Model Card\n\n## Intended use\n")

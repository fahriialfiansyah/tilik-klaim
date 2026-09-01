"""The Isolation Forest baseline over the feature table.

An anomaly score is a statement about how unusual a claim looks against the population the model
was fitted on. It is **not** a statement about anyone's conduct, and on its own it never names a
reason — which is why the aggregation in `ranking.py` can only ever use it to move a case up a
queue, beside reasons the rules layer produced.
"""
from __future__ import annotations

import pytest
from tilik_model.anomaly import PeerAnomaly
from tilik_model.dataset import build_contexts
from tilik_model.features import FeatureExtractor, PeerProfile


@pytest.fixture(scope="module")
def rows(bundles):
    extractor = FeatureExtractor(PeerProfile.fit(bundles))
    contexts = build_contexts(bundles)
    return tuple(
        extractor.extract(
            bundle, contexts[bundle.bundle_id].history, contexts[bundle.bundle_id].peer_documents
        )
        for bundle in bundles
    )


@pytest.fixture(scope="module")
def fitted(rows):
    return PeerAnomaly.fit(rows)


def test_every_score_is_bounded(fitted, rows) -> None:
    for row in rows[:80]:
        score = fitted.score(row)
        assert 0.0 <= score.value <= 1.0


def test_scoring_is_deterministic(fitted, rows) -> None:
    """A queue that reorders itself between two identical runs is not reviewable."""
    for row in rows[:40]:
        assert fitted.score(row) == fitted.score(row)


def test_two_fits_on_the_same_data_agree(rows) -> None:
    """The random state is pinned, so the forest is a function of its input and nothing else."""
    first, second = PeerAnomaly.fit(rows), PeerAnomaly.fit(rows)
    for row in rows[:25]:
        assert first.score(row).value == pytest.approx(second.score(row).value, abs=1e-12)


def test_an_extreme_row_scores_above_the_population_median(fitted, rows) -> None:
    """The model must actually separate something, or it is an expensive constant."""
    typical = sorted(fitted.score(row).value for row in rows)
    median = typical[len(typical) // 2]

    extreme = rows[0].model_copy(
        update={"values": tuple(value * 50.0 + 25.0 for value in rows[0].values)}
    )
    assert fitted.score(extreme).value > median


def test_fitting_on_nothing_produces_an_inert_model(rows) -> None:
    """An empty training partition is a legitimate input, not an exception."""
    inert = PeerAnomaly.fit(())
    assert not inert.is_fitted
    assert inert.score(rows[0]).value == 0.0


def test_a_cold_start_row_still_scores(fitted, rows) -> None:
    """An unseen facility imputes its peer columns; the forest must accept that row."""
    imputed = rows[0].model_copy(update={"imputed": ("line_count_peer_deviation",)})
    assert 0.0 <= fitted.score(imputed).value <= 1.0


def test_a_row_of_the_wrong_width_is_refused(fitted, rows) -> None:
    """Silently padding a short row would score a claim against columns nobody computed."""
    with pytest.raises(ValueError, match="feature"):
        fitted.score(rows[0].model_copy(update={"values": rows[0].values[:-1]}))

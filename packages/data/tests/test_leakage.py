"""The leakage probe, and proof that it can actually detect a leak.

A probe that never fires is not a control. Half of these tests deliberately plant a leak and
assert the probe catches it — otherwise a clean result would prove nothing about the probe.
"""
from __future__ import annotations

import pytest

from tilik_data.corpus import InjectionPlan, build_corpus
from tilik_data.leakage import CHANCE_TOLERANCE, probe, strip_injector_traces

SEED = 20260902
PLAN = InjectionPlan(20, 0.05, {"obvious": 0.3, "moderate": 0.5, "subtle": 0.2})


@pytest.fixture(scope="module")
def corpus():
    return build_corpus(SEED, claims=400, participants=100, providers=6, plan=PLAN)


def test_probe_detects_a_planted_leak(corpus) -> None:
    """Raw injector output *should* leak: ids carry an injector suffix and order is grouped."""
    injected = corpus.injected_bundle_ids()
    leaky = tuple(
        bundle for bundle in corpus.bundles if bundle.bundle_id in injected
    ) + tuple(
        bundle for bundle in corpus.bundles if bundle.bundle_id not in injected
    )
    report = probe(leaky, injected)
    assert report.leaked, (
        "the probe failed to notice a corpus sorted by injection status; "
        f"{report.summary()}"
    )


def test_stripping_traces_removes_the_leak(corpus) -> None:
    """The control that matters: after regenerating ids and reordering, the tell is gone."""
    injected = corpus.injected_bundle_ids()
    cleaned = strip_injector_traces(corpus.bundles, SEED)

    # Ids changed, so map the injection set through the same transformation.
    import hashlib

    renamed_injected = frozenset(
        f"BND-{hashlib.sha256(f'{SEED}:{bundle_id}'.encode()).hexdigest()[:12]}"
        for bundle_id in injected
    )
    report = probe(cleaned, renamed_injected)
    assert not report.leaked, f"corpus still leaks after stripping: {report.summary()}"
    assert report.margin <= CHANCE_TOLERANCE


def test_stripped_ids_no_longer_announce_the_injector(corpus) -> None:
    """`BND-00042-R173` tells a reader both that it was injected and by which injector."""
    cleaned = strip_injector_traces(corpus.bundles, SEED)
    for bundle in cleaned:
        assert "-R" not in bundle.bundle_id[4:]
        assert "-U" not in bundle.bundle_id[4:]


def test_stripping_preserves_the_records_themselves(corpus) -> None:
    """Only identity and ordering change; the claim content must survive intact."""
    cleaned = strip_injector_traces(corpus.bundles, SEED)
    assert len(cleaned) == len(corpus.bundles)
    original_claims = sorted(bundle.claim.claim_id for bundle in corpus.bundles)
    cleaned_claims = sorted(bundle.claim.claim_id for bundle in cleaned)
    assert original_claims == cleaned_claims


def test_stripping_is_deterministic(corpus) -> None:
    assert strip_injector_traces(corpus.bundles, SEED) == strip_injector_traces(
        corpus.bundles, SEED
    )


def test_report_states_which_features_it_used(corpus) -> None:
    """A probe result is only interpretable if it names what it was allowed to see."""
    report = probe(corpus.bundles, corpus.injected_bundle_ids())
    assert report.feature_names == (
        "serialisation_position",
        "id_length",
        "id_character_sum",
    )
    assert "probe accuracy" in report.summary()


def test_empty_corpus_is_handled(corpus) -> None:
    assert not probe((), frozenset()).leaked

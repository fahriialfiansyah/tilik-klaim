"""The leakage probe, and proof that it can actually detect a leak.

A probe that never fires is not a control. Half of these tests deliberately plant a leak and
assert the probe catches it — otherwise a clean result would prove nothing about the probe.
"""
from __future__ import annotations

import pytest

from tilik_data.corpus import InjectionPlan, build_corpus
from tilik_data.leakage import (
    CHANCE_TOLERANCE,
    carries_injector_suffix,
    injector_free_ids,
    probe,
    rename_labels,
    strip_injector_traces,
)

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
    cleaned = strip_injector_traces(corpus.bundles, SEED)

    # Ids changed, so read the injection set from labels carried through the same rename.
    renaming = injector_free_ids(corpus.bundles, SEED)
    renamed_injected = rename_labels(corpus.labels, renaming).bundle_ids()

    report = probe(cleaned, renamed_injected)
    assert not report.leaked, f"corpus still leaks after stripping: {report.summary()}"
    assert report.margin <= CHANCE_TOLERANCE


def test_stripped_ids_no_longer_announce_the_injector(corpus) -> None:
    """`BND-00042-R173` tells a reader both that it was injected and by which injector.

    Checked over **every** identifier in the bundle, not just its own. The injectors stamp the
    same suffix onto the claim and its lines, so scrubbing the bundle id alone would leave
    `CLM-00042-R173` sitting one level down saying exactly the same thing.
    """
    cleaned = strip_injector_traces(corpus.bundles, SEED)
    for bundle in cleaned:
        marked = [
            value
            for value in _identifiers(bundle.model_dump())
            if carries_injector_suffix(value)
        ]
        assert not marked, f"{bundle.bundle_id} still carries {marked}"


def test_stripping_preserves_the_records_themselves(corpus) -> None:
    """Only identity and ordering change; the claim content must survive intact.

    Content is compared on fields that are *not* identifiers. Claim ids used to stand in for
    content here, which quietly asserted that they are never rewritten — the very gap that let
    the injector suffix reach the published corpus.
    """
    cleaned = strip_injector_traces(corpus.bundles, SEED)
    assert len(cleaned) == len(corpus.bundles)
    assert sorted(map(_content, cleaned)) == sorted(map(_content, corpus.bundles))


def test_rename_carries_through_to_the_labels(corpus) -> None:
    """Ground truth written in a different alphabet from the corpus can score nothing."""
    cleaned = strip_injector_traces(corpus.bundles, SEED)
    renaming = injector_free_ids(corpus.bundles, SEED)
    labels = rename_labels(corpus.labels, renaming)

    published = {bundle.bundle_id for bundle in cleaned}
    assert labels.bundle_ids() <= published
    assert len(labels.labels) == len(corpus.labels.labels)
    for label in labels.labels:
        assert label.source_bundle_id in published


def test_free_text_is_not_mistaken_for_an_identifier() -> None:
    """A note that mentions a code must survive the scrub unedited."""
    assert carries_injector_suffix("BND-00042-R173")
    assert carries_injector_suffix("LN-00042-1-U798")
    assert not carries_injector_suffix("BND-00042")
    assert not carries_injector_suffix("Pasien kontrol ulang, lihat BND-00042-R173.")


def _identifiers(node: object):
    """Every string in a dumped bundle, so an assertion can look at all of them."""
    if isinstance(node, dict):
        for value in node.values():
            yield from _identifiers(value)
    elif isinstance(node, list | tuple):
        for item in node:
            yield from _identifiers(item)
    elif isinstance(node, str):
        yield node


def _content(bundle) -> tuple:
    """A fingerprint of everything that is not an identifier."""
    return (
        bundle.claim.participant_id,
        bundle.claim.provider_id,
        bundle.claim.submitted_at,
        bundle.claim.total_amount,
        tuple(sorted(str(line.line_amount) for line in bundle.lines)),
        tuple(sorted(document.text_hash for document in bundle.documents)),
    )


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

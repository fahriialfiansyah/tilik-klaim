"""Partition isolation, demo separation, and the frozen test set."""
from __future__ import annotations

import pytest

from tilik_data.corpus import InjectionPlan, build_corpus
from tilik_data.split import (
    GOLD_BUNDLE_IDS,
    SplitRatios,
    assert_test_set_unchanged,
    group_key,
    make_split,
)

SEED = 20260902
PLAN = InjectionPlan(12, 0.05, {"obvious": 0.3, "moderate": 0.5, "subtle": 0.2})


@pytest.fixture(scope="module")
def corpus():
    return build_corpus(SEED, claims=400, participants=100, providers=6, plan=PLAN)


def test_no_group_spans_two_partitions(corpus) -> None:
    """The property the whole split exists to guarantee."""
    split = make_split(corpus.bundles, seed=SEED)
    seen: dict[str, str] = {}
    for bundle in corpus.bundles:
        partition = split.partition_of(bundle.bundle_id)
        if partition is None:
            continue
        key = group_key(bundle, 30)
        if key in seen:
            assert seen[key] == partition, f"group {key} spans {seen[key]} and {partition}"
        seen[key] = partition


def test_every_bundle_lands_in_exactly_one_partition(corpus) -> None:
    split = make_split(corpus.bundles, seed=SEED)
    assert not (split.train & split.validation)
    assert not (split.train & split.test)
    assert not (split.validation & split.test)
    covered = split.all_partitioned() | split.excluded_demo
    assert covered == {bundle.bundle_id for bundle in corpus.bundles}


def test_ratios_are_roughly_respected(corpus) -> None:
    split = make_split(corpus.bundles, seed=SEED)
    total = len(split.all_partitioned())
    assert 0.45 < len(split.train) / total < 0.75
    assert 0.10 < len(split.validation) / total < 0.32
    assert 0.10 < len(split.test) / total < 0.32


def test_gold_fixtures_never_enter_a_metric_set(corpus) -> None:
    """Demo records are the ones most likely to have been looked at while tuning."""
    with_gold = corpus.bundles + tuple(
        corpus.bundles[0].model_copy(update={"bundle_id": gold}) for gold in GOLD_BUNDLE_IDS
    )
    split = make_split(with_gold, seed=SEED)
    assert split.excluded_demo == GOLD_BUNDLE_IDS
    for gold in GOLD_BUNDLE_IDS:
        assert split.partition_of(gold) is None


def test_assignment_is_stable_when_the_corpus_grows(corpus) -> None:
    """Adding records must not silently move an existing group and invalidate a measurement."""
    smaller = make_split(corpus.bundles[:200], seed=SEED)
    larger = make_split(corpus.bundles, seed=SEED)
    for bundle in corpus.bundles[:200]:
        if bundle.bundle_id in smaller.all_partitioned():
            assert smaller.partition_of(bundle.bundle_id) == larger.partition_of(bundle.bundle_id)


def test_frozen_test_set_change_is_detectable(corpus) -> None:
    split = make_split(corpus.bundles, seed=SEED)
    assert_test_set_unchanged(split)

    tampered = type(split)(
        train=split.train,
        validation=split.validation,
        test=split.test | {"BND-SNUCK-IN"},
        excluded_demo=split.excluded_demo,
        frozen_at=split.frozen_at,
    )
    with pytest.raises(RuntimeError, match="frozen test set has changed"):
        assert_test_set_unchanged(tampered)


def test_ratios_must_sum_to_one() -> None:
    with pytest.raises(ValueError, match="sum to 1.0"):
        SplitRatios(train=0.5, validation=0.2, test=0.2)

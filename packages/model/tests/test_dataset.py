"""Loading the published artifacts, and the group-split guarantee the model must respect.

Two different properties are checked here and they are easy to confuse.

The **split** guarantees that a `(participant, facility, time block)` group never straddles a
partition. That is what `packages/data` promises and it holds.

The **model** needs something stronger for fitting: it must not have seen a participant who
appears downstream at all. One participant can legitimately land in two partitions — at a
different facility, or a different month — so the split's guarantee does not give the model
what it needs, and the gap is measured here rather than assumed away.
"""
from __future__ import annotations

import pytest
from tilik_model.dataset import (
    TEST,
    TRAIN,
    VALIDATION,
    ArtifactsDoNotJoin,
    assert_artifacts_join,
    build_contexts,
    load_build,
    participants_of,
    uncontaminated_training_bundles,
)

BLOCK_DAYS = 30
SECONDS_PER_DAY = 86_400


@pytest.fixture(scope="module")
def artifacts(build_dir):
    return load_build(build_dir)


def test_the_published_artifacts_load_and_join(artifacts) -> None:
    assert artifacts.bundles
    assert artifacts.labelled_bundle_ids <= {b.bundle_id for b in artifacts.bundles}
    assert artifacts.dataset_digest() != "unset"


def test_a_corpus_that_does_not_join_its_split_is_refused(artifacts) -> None:
    """The Sprint 01 defect, turned into a load-time error for every future consumer."""
    broken = type(artifacts)(
        bundles=artifacts.bundles,
        partitions={
            TRAIN: frozenset({"BND-DOES-NOT-EXIST"}),
            VALIDATION: frozenset(),
            TEST: frozenset(),
        },
        excluded_demo=frozenset(),
        labelled_bundle_ids=frozenset(),
        manifest={},
    )
    with pytest.raises(ArtifactsDoNotJoin, match="absent from the corpus"):
        assert_artifacts_join(broken)


def test_no_group_spans_two_partitions(artifacts) -> None:
    """The guarantee `packages/data` makes: related claims never straddle a boundary."""
    seen: dict[str, str] = {}
    for name in (TRAIN, VALIDATION, TEST):
        for bundle in artifacts.partition(name):
            key = _group_key(bundle)
            if key in seen:
                assert seen[key] == name, f"group {key} spans {seen[key]} and {name}"
            seen[key] = name


def test_partitions_do_not_overlap(artifacts) -> None:
    train, validation, test = (artifacts.partitions[n] for n in (TRAIN, VALIDATION, TEST))
    assert not train & validation
    assert not train & test
    assert not validation & test


def test_training_never_sees_a_participant_from_validation_or_test(artifacts) -> None:
    """The property the model needs, enforced on the training side without re-cutting a split."""
    kept, dropped = uncontaminated_training_bundles(artifacts)
    downstream = participants_of(artifacts.partition(VALIDATION)) | participants_of(
        artifacts.partition(TEST)
    )
    assert not participants_of(kept) & downstream
    assert kept, "filtering left no training data at all"
    assert len(kept) + len(dropped) == len(artifacts.partition(TRAIN))


def test_the_contamination_being_filtered_is_real_and_measured(artifacts) -> None:
    """If this ever drops to zero the filter is dead code, and the comment above is wrong."""
    _, dropped = uncontaminated_training_bundles(artifacts)
    assert dropped, (
        "no training bundle shares a participant with validation or test — either the split "
        "changed to group by participant, or this filter is no longer doing anything"
    )


def test_history_never_contains_the_bundle_itself_or_its_future(artifacts) -> None:
    """A claim that can see its own future would score its own duplicate as prior evidence."""
    contexts = build_contexts(artifacts.bundles)
    for bundle in artifacts.bundles:
        context = contexts[bundle.bundle_id]
        for past in context.history:
            assert past.bundle_id != bundle.bundle_id
            assert past.claim.submitted_at <= bundle.claim.submitted_at


def test_history_stays_within_one_participant_and_one_facility(artifacts) -> None:
    """Repeat billing and unbundling are per-participant patterns at one place."""
    contexts = build_contexts(artifacts.bundles)
    for bundle in artifacts.bundles:
        for past in contexts[bundle.bundle_id].history:
            assert past.claim.participant_id == bundle.claim.participant_id
            assert past.claim.provider_id == bundle.claim.provider_id


def test_peer_documents_cross_participants_but_never_carry_a_bundle(artifacts) -> None:
    """Cloning is a facility-level pattern. Notes cross that boundary; whole bundles never do."""
    contexts = build_contexts(artifacts.bundles)
    own_documents = {
        bundle.bundle_id: {document.document_id for document in bundle.documents}
        for bundle in artifacts.bundles
    }
    for bundle in artifacts.bundles:
        peers = contexts[bundle.bundle_id].peer_documents
        assert not {document.document_id for document in peers} & own_documents[bundle.bundle_id]
        from tilik_domain.canonical import DocumentRef

        assert all(isinstance(document, DocumentRef) for document in peers)


def _group_key(bundle) -> str:
    block = int(bundle.claim.submitted_at.timestamp() // (BLOCK_DAYS * SECONDS_PER_DAY))
    return f"{bundle.claim.participant_id}|{bundle.claim.provider_id}|{block}"

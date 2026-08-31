"""The clean corpus must be reproducible and internally consistent.

If these fail, nothing downstream means anything: an injection into an inconsistent record
produces a label that misdescribes why a detector fired.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from tilik_data.amounts import ROUNDING_TOLERANCE, claim_total, money, reconciles
from tilik_data.corpus import BaseCorpusInconsistent, verify_clean
from tilik_data.generator import corpus_hash, generate_bundle, generate_corpus

SEED = 20260902


@pytest.fixture(scope="module")
def corpus():
    return generate_corpus(SEED, 200, participant_count=60, provider_count=6)


def test_same_seed_produces_identical_output(corpus) -> None:
    again = generate_corpus(SEED, 200, participant_count=60, provider_count=6)
    assert corpus_hash(corpus) == corpus_hash(again)


def test_a_different_seed_produces_different_output(corpus) -> None:
    other = generate_corpus(SEED + 1, 200, participant_count=60, provider_count=6)
    assert corpus_hash(corpus) != corpus_hash(other)


def test_one_bundle_regenerates_identically_outside_its_run(corpus) -> None:
    """Per-bundle seeding: bundle n must not depend on how many preceded it."""
    alone = generate_bundle(SEED, 42, participant_count=60, provider_count=6)
    assert alone == corpus[42]


def test_no_dangling_references(corpus) -> None:
    for bundle in corpus:
        assert not bundle.unresolved_refs(), f"{bundle.bundle_id} has dangling refs"


def test_claim_totals_reconcile_within_tolerance(corpus) -> None:
    for bundle in corpus:
        amounts = tuple(line.line_amount for line in bundle.lines)
        assert reconciles(bundle.claim.total_amount, amounts), bundle.bundle_id


def test_no_procedure_precedes_its_encounter(corpus) -> None:
    for bundle in corpus:
        encounters = {e.encounter_id: e for e in bundle.encounters}
        for procedure in bundle.procedures:
            encounter = encounters[procedure.encounter_id]
            assert procedure.performed_at >= encounter.start_at, bundle.bundle_id
            if encounter.end_at:
                assert procedure.performed_at <= encounter.end_at, bundle.bundle_id


def test_every_billed_line_has_supporting_evidence(corpus) -> None:
    """The clean invariant the phantom injector later breaks."""
    for bundle in corpus:
        for line in bundle.lines:
            assert line.supporting_refs, f"{bundle.bundle_id}/{line.line_id} unsupported"


def test_no_duplicate_ids_within_a_bundle(corpus) -> None:
    for bundle in corpus:
        for items, attribute in (
            (bundle.lines, "line_id"),
            (bundle.procedures, "procedure_id"),
            (bundle.charge_items, "charge_item_id"),
        ):
            ids = [getattr(item, attribute) for item in items]
            assert len(ids) == len(set(ids)), f"{bundle.bundle_id} duplicate {attribute}"


def test_bundle_ids_are_unique_across_the_corpus(corpus) -> None:
    ids = [bundle.bundle_id for bundle in corpus]
    assert len(ids) == len(set(ids))


def test_notes_vary_across_encounters(corpus) -> None:
    """If every clean note read alike, the clone detector would fire corpus-wide."""
    texts = [b.documents[0].text for b in corpus if b.documents]
    assert len(texts) > 20, "not enough notes to judge variety"
    assert len(set(texts)) / len(texts) > 0.5, "clean notes are too uniform"


def test_some_bundles_carry_no_note(corpus) -> None:
    """A bundle without a note is ordinary, and the incomplete path needs such records."""
    assert any(not bundle.documents for bundle in corpus)


def test_verify_clean_accepts_the_generated_corpus(corpus) -> None:
    verify_clean(corpus)


def test_verify_clean_rejects_an_unsupported_line(corpus) -> None:
    """The guard must actually bite, or 'verified before injection' means nothing."""
    broken = corpus[0]
    stripped = broken.model_copy(
        update={"lines": tuple(line.model_copy(update={"supporting_refs": ()}) for line in broken.lines)}
    )
    with pytest.raises(BaseCorpusInconsistent, match="without supporting evidence"):
        verify_clean((stripped,))


def test_verify_clean_rejects_a_total_mismatch(corpus) -> None:
    broken = corpus[0]
    mismatched = broken.model_copy(
        update={"claim": broken.claim.model_copy(update={"total_amount": money(1)})}
    )
    with pytest.raises(BaseCorpusInconsistent, match="reconcile"):
        verify_clean((mismatched,))


def test_rounding_tolerance_is_named_not_hidden() -> None:
    assert ROUNDING_TOLERANCE == Decimal("0.01")
    amounts = (money("100.00"), money("200.00"))
    assert reconciles(claim_total(amounts) + Decimal("0.01"), amounts)
    assert not reconciles(claim_total(amounts) + Decimal("0.02"), amounts)

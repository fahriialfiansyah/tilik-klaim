"""The character n-gram similarity baseline, and the ways a note can be unusable.

Cloning is a **facility-level** pattern across different participants, so the score is computed
against peer notes rather than the participant's own history. A patient with a recurring
complaint producing near-identical notes is ordinary care, not a signal.
"""
from __future__ import annotations

import pytest
from tilik_domain.canonical import DocumentRef
from tilik_model.dataset import build_contexts
from tilik_model.similarity import (
    MINIMUM_NOTE_CHARACTERS,
    NoteSimilarity,
    SimilarityScore,
)

AUTHORED = "2026-03-01T08:00:00+00:00"


def _document(document_id: str, text: str | None, digest: str = "d") -> DocumentRef:
    return DocumentRef(
        document_id=document_id,
        kind="ringkasan",
        text=text,
        text_hash=digest,
        authored_at=AUTHORED,
        encounter_id="ENC-X",
    )


@pytest.fixture(scope="module")
def fitted(bundles) -> NoteSimilarity:
    notes = [document.text for bundle in bundles for document in bundle.documents]
    return NoteSimilarity.fit([note for note in notes if note])


def test_an_identical_note_scores_at_the_top(fitted) -> None:
    text = "Riwayat keluhan 5 hari. Penilaian klinis menunjuk K29.7. Perkembangan membaik."
    score = fitted.score([_document("DOC-A", text)], [_document("DOC-B", text)])
    assert score.value == pytest.approx(1.0, abs=1e-6)
    assert score.matched_document_id == "DOC-B"


def test_unrelated_notes_score_low(fitted) -> None:
    score = fitted.score(
        [_document("DOC-A", "Pasien datang dengan keluhan nyeri kepala sejak tiga hari.")],
        [_document("DOC-B", "Kontrol rutin kehamilan trimester kedua, tekanan darah normal.")],
    )
    assert score.value < 0.6


def test_no_note_at_all_is_a_zero_not_a_crash(fitted) -> None:
    score = fitted.score([], [_document("DOC-B", "apa pun")])
    assert score == SimilarityScore(value=0.0, matched_document_id=None, comparisons=0)


def test_no_peer_note_is_a_zero_not_a_crash(fitted) -> None:
    score = fitted.score([_document("DOC-A", "sebuah catatan klinis yang cukup panjang")], [])
    assert score.value == 0.0
    assert score.comparisons == 0


def test_a_note_too_short_to_judge_is_skipped(fitted) -> None:
    """Two three-character notes are not evidence of copying; they are not evidence at all."""
    tiny = "ok"
    assert len(tiny) < MINIMUM_NOTE_CHARACTERS
    score = fitted.score([_document("DOC-A", tiny)], [_document("DOC-B", tiny)])
    assert score.value == 0.0
    assert score.comparisons == 0


def test_a_document_without_text_is_skipped(fitted) -> None:
    """`DocumentRef.text` is optional and omitted from list responses."""
    score = fitted.score([_document("DOC-A", None)], [_document("DOC-B", None)])
    assert score.value == 0.0


def test_fitting_on_no_usable_note_produces_an_inert_model() -> None:
    """An empty vocabulary must degrade to "no opinion", never to an exception."""
    inert = NoteSimilarity.fit([])
    assert not inert.is_fitted
    note = "catatan klinis yang panjang"
    score = inert.score([_document("DOC-A", note)], [_document("DOC-B", note)])
    assert score.value == 0.0


def test_scoring_is_deterministic(fitted, bundles) -> None:
    contexts = build_contexts(bundles)
    for bundle in bundles[:15]:
        context = contexts[bundle.bundle_id]
        first = fitted.score(bundle.documents, context.peer_documents)
        second = fitted.score(bundle.documents, context.peer_documents)
        assert first == second


def test_every_score_is_a_bounded_probability_like_number(fitted, bundles) -> None:
    contexts = build_contexts(bundles)
    for bundle in bundles[:40]:
        context = contexts[bundle.bundle_id]
        score = fitted.score(bundle.documents, context.peer_documents)
        assert 0.0 <= score.value <= 1.0


def test_a_shared_template_does_not_reach_certainty(fitted) -> None:
    """Templated documentation is ordinary practice — the score may be high, never a verdict.

    This test records the shape of the risk. The cap that acts on it lives in `ranking.py`;
    similarity alone can never produce the top band, however high this number goes.
    """
    template = "Anamnesis: keluhan utama. Pemeriksaan fisik dalam batas normal. Rencana: kontrol."
    score = fitted.score(
        [_document("DOC-A", template + " Tambahan: pasien mengeluh pusing ringan.")],
        [_document("DOC-B", template + " Tambahan: pasien mengeluh nyeri lutut kiri.")],
    )
    assert score.value > 0.5, "the baseline should notice a shared template"
    assert score.value <= 1.0

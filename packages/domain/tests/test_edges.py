"""Evidence edge invariants — chiefly the confidence contract."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from tilik_domain.canonical import ResourceRef, ResourceType
from tilik_domain.edges import INFERRED_EDGE_TYPES, EdgeType, EvidenceEdge

CLAIM_A = ResourceRef(resource_type=ResourceType.CLAIM, resource_id="CLM-A")
CLAIM_B = ResourceRef(resource_type=ResourceType.CLAIM, resource_id="CLM-B")
LINE = ResourceRef(resource_type=ResourceType.CLAIM_LINE, resource_id="LN-1")


def test_stated_edge_needs_no_confidence() -> None:
    edge = EvidenceEdge(
        edge_type=EdgeType.CONTAINS, source=CLAIM_A, target=LINE, derivation_rule="claim.lines"
    )
    assert edge.confidence is None


def test_inferred_edge_without_confidence_is_rejected() -> None:
    """An inferred edge with no confidence would present a guess as a fact."""
    with pytest.raises(ValidationError, match="must carry a confidence"):
        EvidenceEdge(
            edge_type=EdgeType.POSSIBLE_DUPLICATE_OF,
            source=CLAIM_A,
            target=CLAIM_B,
            derivation_rule="repeat.fingerprint",
        )


def test_stated_edge_with_confidence_is_rejected() -> None:
    """A stated relation with a confidence implies doubt the source does not express."""
    with pytest.raises(ValidationError, match="must not carry a confidence"):
        EvidenceEdge(
            edge_type=EdgeType.CONTAINS,
            source=CLAIM_A,
            target=LINE,
            derivation_rule="claim.lines",
            confidence=0.9,
        )


def test_inferred_edge_with_confidence_is_accepted() -> None:
    edge = EvidenceEdge(
        edge_type=EdgeType.SIMILAR_TO,
        source=ResourceRef(resource_type=ResourceType.DOCUMENT, resource_id="DOC-1"),
        target=ResourceRef(resource_type=ResourceType.DOCUMENT, resource_id="DOC-2"),
        derivation_rule="clone.char_ngram",
        confidence=0.87,
    )
    assert edge.confidence == pytest.approx(0.87)


@pytest.mark.parametrize("bad", [-0.1, 1.1])
def test_confidence_outside_zero_to_one_is_rejected(bad: float) -> None:
    with pytest.raises(ValidationError):
        EvidenceEdge(
            edge_type=EdgeType.SIMILAR_TO,
            source=CLAIM_A,
            target=CLAIM_B,
            derivation_rule="clone.char_ngram",
            confidence=bad,
        )


def test_only_duplicate_and_similarity_edges_are_inferred() -> None:
    assert INFERRED_EDGE_TYPES == {EdgeType.POSSIBLE_DUPLICATE_OF, EdgeType.SIMILAR_TO}


def test_every_edge_records_its_derivation_rule() -> None:
    """Provenance on every edge is what makes 'why was this flagged?' answerable."""
    assert "derivation_rule" in EvidenceEdge.model_fields
    assert "ruleset_version" in EvidenceEdge.model_fields

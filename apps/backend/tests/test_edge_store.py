"""Edge persistence keeps a screen repeatable and an old audit event resolvable."""
from __future__ import annotations

import pytest
from tilik_domain.edges import EdgeType
from tilik_domain.versioning import RULESET_VERSION

from app.service.evidence_graph import build_evidence_graph
from app.store.edges import InMemoryEdgeStore, StoredEdge
from tests.fixtures import SCENARIOS, load


def graph_for(scenario: str):
    fixture = load(scenario)
    return build_evidence_graph(fixture.bundle, history=fixture.history)


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_edges_round_trip_without_loss(scenario: str) -> None:
    """A stored row must rebuild the exact domain edge, confidence included."""
    graph = graph_for(scenario)
    store = InMemoryEdgeStore()
    written = store.replace(graph.bundle_id, RULESET_VERSION, graph.edges)

    assert written == len(graph.edges)
    assert store.edges_for(graph.bundle_id, RULESET_VERSION) == graph.edges


def test_rescreening_replaces_rather_than_appends() -> None:
    """Screening twice must not double the evidence a reviewer sees."""
    graph = graph_for("phantom")
    store = InMemoryEdgeStore()
    store.replace(graph.bundle_id, RULESET_VERSION, graph.edges)
    store.replace(graph.bundle_id, RULESET_VERSION, graph.edges)

    assert len(store.edges_for(graph.bundle_id, RULESET_VERSION)) == len(graph.edges)


def test_a_new_version_leaves_the_previous_slice_intact() -> None:
    """An audit event citing the old edges must keep resolving after a rules change."""
    graph = graph_for("phantom")
    store = InMemoryEdgeStore()
    store.replace(graph.bundle_id, RULESET_VERSION, graph.edges)

    next_version = "9.9.9"
    bumped = tuple(
        edge.model_copy(update={"ruleset_version": next_version}) for edge in graph.edges
    )
    store.replace(graph.bundle_id, next_version, bumped)

    assert store.edges_for(graph.bundle_id, RULESET_VERSION) == graph.edges
    assert len(store.edges_for(graph.bundle_id, next_version)) == len(bumped)
    assert set(store.versions_for(graph.bundle_id)) == {RULESET_VERSION, next_version}


def test_mixing_ruleset_versions_in_one_slice_is_refused() -> None:
    """A slice holding two versions could not be attributed to either. Fail loudly."""
    graph = graph_for("phantom")
    mixed = (*graph.edges, graph.edges[0].model_copy(update={"ruleset_version": "9.9.9"}))
    store = InMemoryEdgeStore()

    with pytest.raises(ValueError, match="unauditable"):
        store.replace(graph.bundle_id, RULESET_VERSION, mixed)


def test_touching_finds_edges_at_either_end() -> None:
    """Case detail asks "what touches this line?" and must get both directions."""
    graph = graph_for("phantom")
    store = InMemoryEdgeStore()
    store.replace(graph.bundle_id, RULESET_VERSION, graph.edges)

    touching = store.touching(graph.bundle_id, RULESET_VERSION, "LN-P1")
    assert touching
    edge_types = {edge.edge_type for edge in touching}
    assert EdgeType.CONTAINS in edge_types, "the claim that bills this line"
    assert EdgeType.SUPPORTED_BY in edge_types, "the evidence this line rests on"


def test_reading_an_unknown_bundle_returns_empty_rather_than_raising() -> None:
    store = InMemoryEdgeStore()
    assert store.edges_for("BND-NOPE", RULESET_VERSION) == ()
    assert store.touching("BND-NOPE", RULESET_VERSION, "LN-1") == ()


def test_stored_rows_split_refs_into_queryable_columns() -> None:
    graph = graph_for("clean")
    row = StoredEdge.from_edge(graph.bundle_id, graph.edges[0])
    assert row.source_id and row.target_id
    assert row.to_edge() == graph.edges[0]

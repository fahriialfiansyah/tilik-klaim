"""Normalized persistence for derived evidence edges.

The working graph lives in memory — it is rebuilt from a bundle whenever it is needed, and
`EvidenceGraph.as_networkx()` is the only place a graph object exists. What gets *stored* is
the flat edge list, one row per edge, because that is what later reads actually ask for:
"which edges touch this claim line?" and "which edges did version X produce?".

Storage is addressed by `(bundle_id, ruleset_version)`. Re-deriving the same bundle at the
same version replaces that slice wholesale rather than appending, so a repeated screen can
never silently double a reviewer's evidence list. Deriving it at a *new* version leaves the
old slice intact, because an audit event that cited the old edges must keep resolving.

The SQLAlchemy implementation lands with `02-ingest-validation/backend/01-bundle-ingestion`,
which owns the engine, the session, and the migrations. Until then this module defines the
contract and an in-memory implementation, so the rule engine can be built and tested against
the same interface it will use in production.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from pydantic import BaseModel, ConfigDict
from tilik_domain.canonical import ResourceRef, ResourceType
from tilik_domain.edges import EdgeType, EvidenceEdge

if TYPE_CHECKING:
    from collections.abc import Iterable


class StoredEdge(BaseModel):
    """One edge flattened into columns.

    Source and target are split into type and id rather than kept as nested refs, so the
    store can be indexed and queried by either end without unpacking a JSON blob.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    bundle_id: str
    edge_type: EdgeType
    source_type: ResourceType
    source_id: str
    target_type: ResourceType
    target_id: str
    derivation_rule: str
    ruleset_version: str
    confidence: float | None = None

    @classmethod
    def from_edge(cls, bundle_id: str, edge: EvidenceEdge) -> StoredEdge:
        return cls(
            bundle_id=bundle_id,
            edge_type=edge.edge_type,
            source_type=edge.source.resource_type,
            source_id=edge.source.resource_id,
            target_type=edge.target.resource_type,
            target_id=edge.target.resource_id,
            derivation_rule=edge.derivation_rule,
            ruleset_version=edge.ruleset_version,
            confidence=edge.confidence,
        )

    def to_edge(self) -> EvidenceEdge:
        """Rebuild the domain edge, so a stored row round-trips without loss."""
        return EvidenceEdge(
            edge_type=self.edge_type,
            source=ResourceRef(resource_type=self.source_type, resource_id=self.source_id),
            target=ResourceRef(resource_type=self.target_type, resource_id=self.target_id),
            derivation_rule=self.derivation_rule,
            ruleset_version=self.ruleset_version,
            confidence=self.confidence,
        )


class EdgeStore(Protocol):
    """What the rule engine needs from edge persistence, and nothing more."""

    def replace(
        self, bundle_id: str, ruleset_version: str, edges: Iterable[EvidenceEdge]
    ) -> int:
        """Store `edges`, discarding any previous slice for this bundle and version."""
        ...

    def edges_for(self, bundle_id: str, ruleset_version: str) -> tuple[EvidenceEdge, ...]:
        """Every edge derived for this bundle at this version, in stored order."""
        ...

    def touching(
        self, bundle_id: str, ruleset_version: str, resource_id: str
    ) -> tuple[EvidenceEdge, ...]:
        """Every edge with `resource_id` at either end — the case-detail lookup."""
        ...


class InMemoryEdgeStore:
    """Reference implementation, used by tests and the seeded demo.

    Rows are copied on write and on read, so a caller can never reach in and mutate stored
    state — the same immutability the domain models enforce.
    """

    def __init__(self) -> None:
        self._slices: dict[tuple[str, str], tuple[StoredEdge, ...]] = {}

    def replace(
        self, bundle_id: str, ruleset_version: str, edges: Iterable[EvidenceEdge]
    ) -> int:
        rows = tuple(StoredEdge.from_edge(bundle_id, edge) for edge in edges)
        mismatched = [row for row in rows if row.ruleset_version != ruleset_version]
        if mismatched:
            raise ValueError(
                f"{len(mismatched)} edge(s) carry a ruleset version other than "
                f"{ruleset_version}; storing them together would make the slice unauditable"
            )
        self._slices[(bundle_id, ruleset_version)] = rows
        return len(rows)

    def edges_for(self, bundle_id: str, ruleset_version: str) -> tuple[EvidenceEdge, ...]:
        rows = self._slices.get((bundle_id, ruleset_version), ())
        return tuple(row.to_edge() for row in rows)

    def touching(
        self, bundle_id: str, ruleset_version: str, resource_id: str
    ) -> tuple[EvidenceEdge, ...]:
        rows = self._slices.get((bundle_id, ruleset_version), ())
        return tuple(
            row.to_edge()
            for row in rows
            if resource_id in (row.source_id, row.target_id)
        )

    def versions_for(self, bundle_id: str) -> tuple[str, ...]:
        """Every version this bundle has been derived at, oldest key order preserved."""
        return tuple(
            version for stored_id, version in self._slices if stored_id == bundle_id
        )

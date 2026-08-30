"""Evidence edges — the nine relations that make a billed line traceable to its support.

Defined in `docs/canonical/03_architecture.md` § Canonical evidence edges.

Every edge records where it came from: the source resources, the rule that derived it, that
rule's version, and a confidence when the relation was inferred rather than stated outright.
Without that, "why was this flagged?" has no answer a reviewer can check — which is the whole
product.
"""
from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from tilik_domain.canonical import ResourceRef
from tilik_domain.versioning import RULESET_VERSION


class EdgeType(StrEnum):
    """The nine canonical edge types."""

    CONTAINS = "CONTAINS"
    """Claim → ClaimLine."""

    BILLED_FROM = "BILLED_FROM"
    """ClaimLine → ChargeItem."""

    FOR_ENCOUNTER = "FOR_ENCOUNTER"
    """Claim or ClaimLine → Encounter."""

    SUPPORTED_BY = "SUPPORTED_BY"
    """ClaimLine → Procedure | Medication | Diagnostic. The core evidence link."""

    HAS_CLINICAL_EVENT = "HAS_CLINICAL_EVENT"
    """Encounter → Condition | Procedure | Medication | Document."""

    AUTHORED_BY = "AUTHORED_BY"
    """Document → Practitioner."""

    PART_OF_ENCOUNTER = "PART_OF_ENCOUNTER"
    """Document → Encounter."""

    POSSIBLE_DUPLICATE_OF = "POSSIBLE_DUPLICATE_OF"
    """Claim → Claim. Inferred; always carries a confidence."""

    SIMILAR_TO = "SIMILAR_TO"
    """Document → Document. Inferred; always carries a confidence."""

    PART_OF_EPISODE = "PART_OF_EPISODE"
    """Claim → Episode."""


INFERRED_EDGE_TYPES: frozenset[EdgeType] = frozenset(
    {EdgeType.POSSIBLE_DUPLICATE_OF, EdgeType.SIMILAR_TO}
)
"""Edges that are computed rather than read. These must always carry a confidence."""


class EvidenceEdge(BaseModel):
    """One derived relation between two canonical resources."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    edge_type: EdgeType
    source: ResourceRef
    target: ResourceRef
    derivation_rule: str
    """Identifier of the rule that produced this edge, so it can be re-derived and audited."""
    ruleset_version: str = RULESET_VERSION
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    """Present when the relation was inferred; absent when it is stated in the source."""

    def model_post_init(self, __context: object) -> None:
        """Enforce the confidence contract at construction time.

        An inferred edge without a confidence would present a guess as a fact — exactly the
        failure mode `docs/canonical/07_privacy_threat_model.md` calls out as concealing
        uncertainty. A stated edge with a confidence is equally wrong: it implies doubt that
        the source does not express.
        """
        is_inferred = self.edge_type in INFERRED_EDGE_TYPES
        if is_inferred and self.confidence is None:
            raise ValueError(
                f"Edge {self.edge_type} is inferred and must carry a confidence"
            )
        if not is_inferred and self.confidence is not None:
            raise ValueError(
                f"Edge {self.edge_type} is stated in the source and must not carry a confidence"
            )

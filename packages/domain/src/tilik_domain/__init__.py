"""TilikKlaim canonical domain.

Owns the shared vocabulary: canonical entities, the reason catalog, evidence edges, and
version identity. Depends on nothing else in this repository — `packages/data`,
`packages/model`, `apps/backend`, and `evaluation/` all depend on it, never the reverse.
"""
from tilik_domain.canonical import (
    CanonicalBundle,
    ClaimHeader,
    ClaimLine,
    DemoMetadata,
    Encounter,
    EventStatus,
    Provenance,
    ResourceRef,
    ResourceType,
)
from tilik_domain.edges import EdgeType, EvidenceEdge
from tilik_domain.reasons import (
    ALLOWED_TRANSITIONS,
    REASON_CATALOG,
    CaseState,
    DispositionAction,
    PriorityBand,
    ReasonCode,
    ReasonDefinition,
    RiskMode,
    codes_for_mode,
    definition_for,
)
from tilik_domain.versioning import ENGINE_VERSION, RULESET_VERSION, SCHEMA_VERSION, EngineIdentity

__all__ = [
    "ALLOWED_TRANSITIONS",
    "CanonicalBundle",
    "CaseState",
    "ClaimHeader",
    "ClaimLine",
    "DemoMetadata",
    "DispositionAction",
    "EdgeType",
    "Encounter",
    "ENGINE_VERSION",
    "EngineIdentity",
    "EventStatus",
    "EvidenceEdge",
    "PriorityBand",
    "Provenance",
    "REASON_CATALOG",
    "RULESET_VERSION",
    "ReasonCode",
    "ReasonDefinition",
    "ResourceRef",
    "ResourceType",
    "RiskMode",
    "SCHEMA_VERSION",
    "codes_for_mode",
    "definition_for",
]

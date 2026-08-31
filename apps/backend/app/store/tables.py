"""Table definitions for everything the service persists.

SQLAlchemy Core rather than the ORM: the domain models are already Pydantic and already
immutable, so an ORM layer would add a second mutable representation of the same facts and a
identity map nobody needs. Rows go in as dictionaries and come back as Pydantic models.

Two choices are worth stating outright.

**`raw_payload` is `TEXT`, not `JSONB`.** JSONB normalises — it reorders keys, drops
insignificant whitespace, and rewrites numbers. That is exactly what "stored verbatim" must not
do: the raw payload exists so a screening result can be re-derived from precisely what arrived,
including any oddity that shaped it. The canonical form is kept separately in `bundle_json`,
where normalisation is welcome.

**Nothing is deleted.** Ingestions and edges are append-or-replace by key; there is no cascade
that would remove an edge an audit event still cites.
"""
from __future__ import annotations

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB

metadata = MetaData()

ID_LENGTH = 128
"""Generous enough for a prefixed UUID or a natural key; short enough to index well."""

VERSION_LENGTH = 32
HASH_LENGTH = 64
"""SHA-256 rendered as hex."""


ingestions = Table(
    "ingestions",
    metadata,
    Column("ingestion_id", String(ID_LENGTH), primary_key=True),
    Column("input_hash", String(HASH_LENGTH), nullable=False),
    Column("idempotency_key", String(256), nullable=False, unique=True),
    Column("status", String(32), nullable=False),
    # Verbatim. See the module docstring for why this is not JSONB.
    Column("raw_payload", Text, nullable=False),
    # The canonical form every downstream component reads. Null when validation failed.
    Column("bundle_json", JSONB, nullable=True),
    Column("issues", JSONB, nullable=False, server_default="[]"),
    Column("completeness_notes", JSONB, nullable=False, server_default="[]"),
    Column("resource_counts", JSONB, nullable=False, server_default="[]"),
    Column("engine_version", String(VERSION_LENGTH), nullable=False),
    Column("ruleset_version", String(VERSION_LENGTH), nullable=False),
    Column("received_at", DateTime(timezone=True), nullable=False),
    Column("case_id", String(ID_LENGTH), nullable=True),
    CheckConstraint(
        "status in ('VALID', 'VALID_WITH_NOTES', 'INVALID')",
        name="ck_ingestions_status",
    ),
    Index("ix_ingestions_input_hash", "input_hash"),
    Index("ix_ingestions_received_at", "received_at"),
)


evidence_edges = Table(
    "evidence_edges",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("bundle_id", String(ID_LENGTH), nullable=False),
    Column("ruleset_version", String(VERSION_LENGTH), nullable=False),
    Column("edge_type", String(48), nullable=False),
    Column("source_type", String(32), nullable=False),
    Column("source_id", String(ID_LENGTH), nullable=False),
    Column("target_type", String(32), nullable=False),
    Column("target_id", String(ID_LENGTH), nullable=False),
    Column("derivation_rule", String(128), nullable=False),
    # Present only on inferred edges; `EvidenceEdge` enforces that contract in the domain.
    Column("confidence", Float, nullable=True),
    CheckConstraint(
        "confidence is null or (confidence >= 0.0 and confidence <= 1.0)",
        name="ck_evidence_edges_confidence_range",
    ),
    # The slice key: every read is "this bundle, at this ruleset version".
    Index("ix_evidence_edges_slice", "bundle_id", "ruleset_version"),
    # Case detail asks "what touches this resource?" from both ends.
    Index("ix_evidence_edges_source", "bundle_id", "ruleset_version", "source_id"),
    Index("ix_evidence_edges_target", "bundle_id", "ruleset_version", "target_id"),
)

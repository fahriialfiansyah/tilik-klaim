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
    Numeric,
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


cases = Table(
    "cases",
    metadata,
    Column("case_id", String(ID_LENGTH), primary_key=True),
    Column("ingestion_id", String(ID_LENGTH), nullable=False),
    Column("bundle_id", String(ID_LENGTH), nullable=False),
    # Optimistic-locking token. A disposition must name the version it acted on.
    Column("case_version", Integer, nullable=False),
    Column("state", String(32), nullable=False),
    Column("band", String(32), nullable=False),
    Column("participant_token", String(ID_LENGTH), nullable=False),
    Column("provider_token", String(ID_LENGTH), nullable=False),
    Column("total_amount", Numeric(18, 2), nullable=False),
    Column("currency", String(8), nullable=False, server_default="IDR"),
    # The whole screening result, so case detail never has to re-screen to explain itself.
    Column("result", JSONB, nullable=False),
    Column("completeness_notes", JSONB, nullable=False, server_default="[]"),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    CheckConstraint("case_version >= 1", name="ck_cases_version_positive"),
    Index("ix_cases_state", "state"),
    Index("ix_cases_band", "band"),
    Index("ix_cases_created_at", "created_at"),
    Index("ix_cases_ingestion", "ingestion_id"),
)


audit_events = Table(
    "audit_events",
    metadata,
    Column("event_id", String(ID_LENGTH), primary_key=True),
    Column("case_id", String(ID_LENGTH), nullable=False),
    Column("event_kind", String(32), nullable=False),
    Column("actor_role", String(64), nullable=False),
    Column("action", String(32), nullable=True),
    Column("structured_reason", Text, nullable=True),
    Column("note", Text, nullable=True),
    Column("evidence", JSONB, nullable=False, server_default="[]"),
    Column("state_before", String(32), nullable=True),
    Column("state_after", String(32), nullable=True),
    Column("case_version_before", Integer, nullable=True),
    Column("case_version_after", Integer, nullable=True),
    # A correction appends and links; the superseded event stays visible.
    Column("supersedes_event_id", String(ID_LENGTH), nullable=True),
    Column("schema_version", String(VERSION_LENGTH), nullable=False),
    Column("ruleset_version", String(VERSION_LENGTH), nullable=False),
    Column("engine_version", String(VERSION_LENGTH), nullable=False),
    Column("dataset_version", String(VERSION_LENGTH), nullable=False),
    Column("occurred_at", DateTime(timezone=True), nullable=False),
    # A disposition without a reason is refused by the database, not merely by the DTO.
    # The UI can be bypassed; this cannot.
    CheckConstraint(
        "event_kind <> 'DISPOSITION' "
        "or (structured_reason is not null and length(btrim(structured_reason)) > 0)",
        name="ck_audit_disposition_requires_reason",
    ),
    Index("ix_audit_case", "case_id", "occurred_at"),
    Index("ix_audit_supersedes", "supersedes_event_id"),
)

APPEND_ONLY_TRIGGER_SQL = """
create or replace function tilik_audit_append_only() returns trigger as $$
begin
    raise exception
        'audit_events is append-only: % is not permitted. Corrections append a superseding '
        'event and leave the original visible.', tg_op;
end;
$$ language plpgsql;

create trigger audit_events_no_update
    before update on audit_events
    for each row execute function tilik_audit_append_only();

create trigger audit_events_no_delete
    before delete on audit_events
    for each row execute function tilik_audit_append_only();
"""
"""Append-only enforced in the database.

A convention is not a control: anything with a connection could rewrite history, and an audit
trail that can be edited is not an audit trail. The trigger refuses UPDATE and DELETE outright,
so a correction has to append a superseding event — which is what keeps the original decision,
and whoever made it, visible.
"""

DROP_APPEND_ONLY_TRIGGER_SQL = """
drop trigger if exists audit_events_no_delete on audit_events;
drop trigger if exists audit_events_no_update on audit_events;
drop function if exists tilik_audit_append_only();
"""

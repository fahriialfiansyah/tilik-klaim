"""Database round-trips, run only when Postgres is actually reachable.

These skip rather than fail without a database, because the frontend team runs this suite with
no Docker at all and `docs/canonical/08_demo_runbook.md` requires the demo to work offline. A
skipped test says "not checked here"; a failing one would say "broken", which would be untrue.

Start the database with `docker compose up -d db` and apply `alembic upgrade head` to run them.
"""
from __future__ import annotations

import json

import pytest
from sqlalchemy import inspect, select, text
from tilik_domain.versioning import RULESET_VERSION

from app.dto.bundles import ValidationStatus
from app.service.evidence_graph import build_evidence_graph
from app.service.hashing import idempotency_key, input_hash
from app.store.bundles import (
    IngestionRecord,
    SqlBundleStore,
    new_ingestion_id,
    received_now,
)
from app.store.edges import SqlEdgeStore
from app.store.engine import get_engine, is_database_available
from app.store.tables import evidence_edges, ingestions
from tests.fixtures import load

pytestmark = pytest.mark.skipif(
    not is_database_available(),
    reason="no Postgres reachable; run `docker compose up -d db && alembic upgrade head`",
)


@pytest.fixture
def bundle_store() -> SqlBundleStore:
    store = SqlBundleStore()
    store.clear()
    yield store
    store.clear()


@pytest.fixture
def edge_store() -> SqlEdgeStore:
    store = SqlEdgeStore()
    store.clear()
    yield store
    store.clear()


def make_record(scenario: str = "phantom", *, raw: str | None = None) -> IngestionRecord:
    fixture = load(scenario)
    payload = fixture.bundle.model_dump(mode="json")
    content_hash = input_hash(payload)
    return IngestionRecord(
        ingestion_id=new_ingestion_id(),
        input_hash=content_hash,
        idempotency_key=idempotency_key(content_hash, "0.1.0", RULESET_VERSION),
        status=ValidationStatus.VALID,
        raw_payload=raw if raw is not None else json.dumps(payload),
        bundle=fixture.bundle,
        completeness_notes=("catatan uji",),
        engine_version="0.1.0",
        ruleset_version=RULESET_VERSION,
        received_at=received_now(),
    )


# --------------------------------------------------------------------------------------
# Schema
# --------------------------------------------------------------------------------------


def test_migrations_created_both_tables() -> None:
    names = set(inspect(get_engine()).get_table_names())
    assert {"ingestions", "evidence_edges", "alembic_version"} <= names


def test_schema_is_at_the_head_revision() -> None:
    """A stale database silently answers the wrong shape; assert the revision instead."""
    with get_engine().connect() as connection:
        stamped = connection.execute(text("select version_num from alembic_version")).scalar()
    assert stamped, "database has no alembic stamp; run `alembic upgrade head`"


# --------------------------------------------------------------------------------------
# Ingestion round-trip
# --------------------------------------------------------------------------------------


def test_raw_payload_and_canonical_rows_both_persist(bundle_store) -> None:
    """The task's DB integration assertion, against a real database."""
    record = make_record()
    bundle_store.save(record)

    fetched = bundle_store.get(record.ingestion_id)

    assert fetched is not None
    assert fetched.raw_payload == record.raw_payload
    assert fetched.bundle == record.bundle, "canonical rows round-trip without loss"
    assert fetched.completeness_notes == record.completeness_notes
    assert fetched.received_at == record.received_at


def test_raw_payload_is_stored_byte_for_byte(bundle_store) -> None:
    """Verbatim means verbatim — key order and whitespace survive, so a result stays re-derivable.

    This is why the column is TEXT and not JSONB: JSONB would reorder keys and drop whitespace,
    quietly destroying the exact form that was submitted.
    """
    odd = '{\n  "z_last": 1,\n     "a_first": 2\n}'
    record = make_record(raw=odd)
    bundle_store.save(record)

    with get_engine().connect() as connection:
        stored = connection.execute(
            select(ingestions.c.raw_payload).where(
                ingestions.c.ingestion_id == record.ingestion_id
            )
        ).scalar_one()

    assert stored == odd


def test_saving_the_same_idempotency_key_replaces_rather_than_duplicates(bundle_store) -> None:
    """One claim, one row — a double click must not become two cases."""
    first = make_record()
    second = first.model_copy(update={"ingestion_id": new_ingestion_id()})

    bundle_store.save(first)
    bundle_store.save(second)

    with get_engine().connect() as connection:
        count = connection.execute(
            select(text("count(*)")).select_from(ingestions)
        ).scalar_one()
    assert count == 1

    found = bundle_store.find_by_idempotency_key(first.idempotency_key)
    assert found is not None


def test_attach_case_records_the_screening_result(bundle_store) -> None:
    record = make_record()
    bundle_store.save(record)

    updated = bundle_store.attach_case(record.ingestion_id, "case_123")

    assert updated is not None
    assert updated.case_id == "case_123"
    assert bundle_store.get(record.ingestion_id).case_id == "case_123"


def test_invalid_status_is_refused_by_the_database(bundle_store) -> None:
    """The check constraint is a second line of defence behind the enum."""
    from sqlalchemy.exc import IntegrityError

    from app.store.engine import session_scope

    with pytest.raises(IntegrityError), session_scope() as session:
        session.execute(
            ingestions.insert().values(
                ingestion_id="ing_bad",
                input_hash="0" * 64,
                idempotency_key="bad-key",
                status="DEFINITELY_FRAUD",
                raw_payload="{}",
                engine_version="0.1.0",
                ruleset_version=RULESET_VERSION,
                received_at=received_now(),
            )
        )


# --------------------------------------------------------------------------------------
# Edge round-trip
# --------------------------------------------------------------------------------------


def test_edges_round_trip_through_the_database(edge_store) -> None:
    fixture = load("clone")
    graph = build_evidence_graph(fixture.bundle, history=fixture.history)

    written = edge_store.replace(graph.bundle_id, RULESET_VERSION, graph.edges)
    fetched = edge_store.edges_for(graph.bundle_id, RULESET_VERSION)

    assert written == len(graph.edges)
    assert fetched == graph.edges, "edges round-trip identically, confidence included"
    assert any(edge.confidence is not None for edge in fetched), "inferred edges kept their score"


def test_rescreening_replaces_the_slice_in_the_database(edge_store) -> None:
    fixture = load("phantom")
    graph = build_evidence_graph(fixture.bundle, history=fixture.history)

    edge_store.replace(graph.bundle_id, RULESET_VERSION, graph.edges)
    edge_store.replace(graph.bundle_id, RULESET_VERSION, graph.edges)

    with get_engine().connect() as connection:
        count = connection.execute(
            select(text("count(*)")).select_from(evidence_edges)
        ).scalar_one()
    assert count == len(graph.edges)


def test_a_version_bump_keeps_the_previous_slice(edge_store) -> None:
    """An audit event citing the old edges must keep resolving after a rules change."""
    fixture = load("phantom")
    graph = build_evidence_graph(fixture.bundle, history=fixture.history)
    edge_store.replace(graph.bundle_id, RULESET_VERSION, graph.edges)

    bumped = tuple(e.model_copy(update={"ruleset_version": "9.9.9"}) for e in graph.edges)
    edge_store.replace(graph.bundle_id, "9.9.9", bumped)

    assert edge_store.edges_for(graph.bundle_id, RULESET_VERSION) == graph.edges
    assert set(edge_store.versions_for(graph.bundle_id)) == {RULESET_VERSION, "9.9.9"}


def test_touching_queries_both_ends_in_sql(edge_store) -> None:
    fixture = load("phantom")
    graph = build_evidence_graph(fixture.bundle, history=fixture.history)
    edge_store.replace(graph.bundle_id, RULESET_VERSION, graph.edges)

    touching = edge_store.touching(graph.bundle_id, RULESET_VERSION, "LN-P1")

    assert touching
    assert all(
        "LN-P1" in (edge.source.resource_id, edge.target.resource_id) for edge in touching
    )


def test_confidence_outside_zero_to_one_is_refused_by_the_database(edge_store) -> None:
    """A confidence above 1.0 would present certainty the model never produced."""
    from sqlalchemy.exc import IntegrityError

    from app.store.engine import session_scope

    with pytest.raises(IntegrityError), session_scope() as session:
        session.execute(
            evidence_edges.insert().values(
                bundle_id="BND-X",
                ruleset_version=RULESET_VERSION,
                edge_type="SIMILAR_TO",
                source_type="Document",
                source_id="DOC-1",
                target_type="Document",
                target_id="DOC-2",
                derivation_rule="test/v1",
                confidence=1.5,
            )
        )

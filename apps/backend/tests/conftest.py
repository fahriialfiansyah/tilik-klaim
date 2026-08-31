"""Shared fixtures.

Every store is cleared around every test. They are process-wide singletons chosen once by
`app.store.registry`, and against Postgres they are genuinely shared state — a test that leaves
rows behind changes the next test's answer.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.store.registry import (
    get_audit_store,
    get_bundle_store,
    get_case_store,
    get_edge_store,
)


@pytest.fixture(autouse=True)
def clean_stores():
    stores = (get_bundle_store(), get_case_store(), get_audit_store(), get_edge_store())
    for store in stores:
        store.clear()
    yield
    for store in stores:
        store.clear()


@pytest.fixture
def api() -> TestClient:
    return TestClient(app)

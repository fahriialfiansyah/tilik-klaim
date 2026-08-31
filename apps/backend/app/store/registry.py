"""Which store implementation the app uses, resolved once per process.

The service prefers Postgres and falls back to the in-memory stores when no database answers.
That fallback is not a convenience — `docs/canonical/08_demo_runbook.md` requires the demo to
run without an external network, and the frontend team runs the API's tests with no database at
all. A hard dependency on Postgres would make both impossible.

The choice is made once and cached, so a request never pays for a connectivity probe and the
two stores can never disagree about where a given ingestion lives. Once a SQL store is chosen,
its errors propagate: falling back mid-request would hide a real outage behind a store that
silently forgets everything.
"""
from __future__ import annotations

import logging
from functools import lru_cache

from app.store.bundles import BundleStore, InMemoryBundleStore, SqlBundleStore
from app.store.edges import EdgeStore, InMemoryEdgeStore, SqlEdgeStore
from app.store.engine import is_database_available

logger = logging.getLogger(__name__)


@lru_cache
def use_database() -> bool:
    """Probe once, remember the answer, and say which way it went."""
    available = is_database_available()
    logger.info("store backend selected: %s", "postgres" if available else "in-memory")
    return available


@lru_cache
def get_bundle_store() -> BundleStore:
    return SqlBundleStore() if use_database() else InMemoryBundleStore()


@lru_cache
def get_edge_store() -> EdgeStore:
    return SqlEdgeStore() if use_database() else InMemoryEdgeStore()


def reset_stores() -> None:
    """Forget the cached choice so a test can re-probe. Not used in a request path."""
    use_database.cache_clear()
    get_bundle_store.cache_clear()
    get_edge_store.cache_clear()

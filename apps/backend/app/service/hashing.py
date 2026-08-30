"""Deterministic content hashing for submitted bundles.

The hash is what makes a screening result reproducible and idempotent, so it has to depend on
the *content* of a bundle and nothing else. Two submissions that differ only in key order,
whitespace, or the timezone a timestamp was written in are the same bundle, and must hash the
same. Two submissions that differ in a billed amount must not.

Timezone rule, stated once and applied everywhere: **every timestamp is normalised to UTC
before hashing, and a timestamp with no offset is read as UTC.** Claims cross time zones and
submitters serialise dates inconsistently; without one rule, the same claim would hash
differently depending on who exported it.
"""
from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

CANONICAL_SEPARATORS = (",", ":")
"""No incidental whitespace in the hashed form."""


def normalise_timestamp(value: datetime) -> str:
    """Render a timestamp in the one form the hash recognises.

    A naive timestamp is treated as UTC rather than rejected: submitters routinely omit the
    offset, and refusing the bundle would be a worse answer than reading it consistently.
    """
    moment = value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    return moment.astimezone(UTC).isoformat()


def canonical_json(payload: Any) -> str:
    """Serialise to the one form that gets hashed: sorted keys, no incidental whitespace."""
    return json.dumps(
        payload,
        sort_keys=True,
        separators=CANONICAL_SEPARATORS,
        ensure_ascii=False,
        default=_encode,
    )


def _encode(value: Any) -> str:
    if isinstance(value, datetime):
        return normalise_timestamp(value)
    return str(value)


def input_hash(payload: Any) -> str:
    """SHA-256 over the canonical form.

    Used as the idempotency key: the same hash at the same engine version must return the
    existing result rather than create a second case for one claim.
    """
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def idempotency_key(content_hash: str, engine_version: str, ruleset_version: str) -> str:
    """What "already screened" means.

    A version bump deliberately produces a new key. Re-screening the same bundle under new
    rules is a legitimately different result, and reusing the old one would silently present a
    stale verdict as current.
    """
    return f"{content_hash}:{engine_version}:{ruleset_version}"

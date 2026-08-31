#!/usr/bin/env python3
"""Write the live OpenAPI document to `docs/api/openapi.json`.

The file is a **generated artifact**, and regenerating it was a manual step nobody remembered:
it was written once when the contract was frozen in sprint 02 and then drifted for two sprints,
still describing `ReasonDto` without its counter-evidence notes and `/v1/cases` with ingest-only
error codes it never returns. A spec that has quietly stopped matching the service is worse than
no spec — a generated client compiles against it and fails at runtime.

Run it after any change to a router or a DTO:

    cd apps/backend && uv run python scripts/export_openapi.py

The frozen contract itself lives in `tests/test_api_contract.py` and the committed fixtures under
`tests/fixtures/api/`, both of which read the live app rather than this file. This is
documentation, not the source of truth.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402

TARGET = Path(__file__).resolve().parents[3] / "docs" / "api" / "openapi.json"


def main() -> int:
    # Sorted and ASCII-escaped so a regeneration produces a diff of real changes rather than of
    # key ordering or encoding.
    document = json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n"
    TARGET.write_text(document, encoding="utf-8")
    print(f"Wrote {TARGET} ({len(document):,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

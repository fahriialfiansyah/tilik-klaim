#!/usr/bin/env python3
"""Export the five gold scenarios as demo payloads the ingest screen can submit.

The ingest screen offers five curated cases that load "tanpa unggah" (`brief/01` § 2.1). They
have to be *the same five* the backend's gold fixtures describe, or the demo would show a
system behaving differently from the one the tests cover.

Two things are deliberate about the shape written here.

**The answer key is stripped.** A gold fixture carries `expected_reason_codes` and
`expected_evidence_complete` beside the bundle — kept outside `CanonicalBundle` precisely so no
detector can reach them (`docs/canonical/04_data_card.md` § Leakage controls). Shipping them to
a browser would put the expected answer one devtools panel away from anyone watching the demo.
Only `demo`, `history`, and `bundle` cross over.

**`history` comes along.** Repeat billing, cloned documentation, and unbundling are only visible
*across* claims, so those three scenarios need their prior bundle ingested first — exactly what
`scripts/seed_dev.py` does. The ingest screen submits the history, then the bundle, and says so
on screen rather than doing it silently.

    cd apps/backend && uv run python scripts/export_demo_samples.py

`tests/test_demo_samples.py` fails if the exported files drift from the fixtures, so a changed
scenario cannot quietly leave the demo showing the old one.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.fixtures import SCENARIOS, load  # noqa: E402

TARGET_DIR = Path(__file__).resolve().parents[3] / "apps" / "web" / "public" / "samples"


def payload_for(scenario: str) -> dict:
    """The submittable part of a gold fixture. Never its expected outcome."""
    fixture = load(scenario)
    return {
        "scenario": fixture.scenario,
        "demo": fixture.demo.model_dump(mode="json"),
        "history": [bundle.model_dump(mode="json") for bundle in fixture.history],
        "bundle": fixture.bundle.model_dump(mode="json"),
    }


def main() -> int:
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    for scenario in SCENARIOS:
        document = json.dumps(payload_for(scenario), indent=2, sort_keys=True) + "\n"
        (TARGET_DIR / f"{scenario}.json").write_text(document, encoding="utf-8")
        print(f"  {scenario:10s} {len(document):>7,} bytes")

    index = json.dumps(
        [
            {
                "scenario": scenario,
                "label": load(scenario).demo.scenario_label,
                "description": load(scenario).demo.description,
                "history_count": len(load(scenario).history),
            }
            for scenario in SCENARIOS
        ],
        indent=2,
        ensure_ascii=False,
    ) + "\n"
    (TARGET_DIR / "index.json").write_text(index, encoding="utf-8")
    print(f"  {'index':10s} {len(index):>7,} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

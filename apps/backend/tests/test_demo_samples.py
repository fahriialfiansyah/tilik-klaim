"""The ingest screen's five demo payloads must stay the five gold scenarios.

`apps/web/public/samples/` is a **generated artifact**, written by
`scripts/export_demo_samples.py`. Generated files drift the moment regenerating them becomes a
step somebody has to remember — `docs/api/openapi.json` sat two sprints out of date for exactly
that reason. These tests make the drift a failing build instead.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from scripts.export_demo_samples import TARGET_DIR, payload_for
from tests.fixtures import SCENARIOS, load

ANSWER_KEY_FIELDS = ("expected_reason_codes", "expected_evidence_complete")


def _exported(scenario: str) -> dict:
    path = TARGET_DIR / f"{scenario}.json"
    assert path.exists(), f"{path} is missing — run scripts/export_demo_samples.py"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_the_exported_sample_matches_its_gold_fixture(scenario: str) -> None:
    """A changed scenario must not leave the demo quietly showing the old one."""
    assert _exported(scenario) == payload_for(scenario), (
        f"{scenario}.json is stale — run `uv run python scripts/export_demo_samples.py`"
    )


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_no_sample_ships_its_answer_key_to_the_browser(scenario: str) -> None:
    """The expected reason codes live outside `CanonicalBundle` so no detector can reach them.

    Shipping them to a browser would undo that: anyone watching the demo could read the
    expected answer out of a network response before the screening ran.
    """
    raw = (TARGET_DIR / f"{scenario}.json").read_text(encoding="utf-8")
    for field in ANSWER_KEY_FIELDS:
        assert field not in raw, f"{scenario}.json leaks the answer key field {field!r}"


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_a_sample_carries_the_history_its_rules_need(scenario: str) -> None:
    """Cross-claim modes are invisible without the prior claim.

    Repeat billing, cloned documentation, and unbundling are only detectable *across* claims. A
    sample exported without its history would ingest cleanly and screen to nothing — a demo
    case that silently proves the opposite of what it is there to show.
    """
    exported = _exported(scenario)
    assert len(exported["history"]) == len(load(scenario).history)


def test_the_index_lists_every_scenario_with_its_working_language_label() -> None:
    index = json.loads((TARGET_DIR / "index.json").read_text(encoding="utf-8"))
    assert [entry["scenario"] for entry in index] == list(SCENARIOS)
    for entry in index:
        assert entry["label"], f"{entry['scenario']} has no label for the screen to show"
        assert entry["description"]


def test_the_export_target_is_inside_the_web_app() -> None:
    """Guards the relative path, which breaks silently if this file is ever moved."""
    assert TARGET_DIR == pathlib.Path(__file__).resolve().parents[3] / "apps" / "web" / "public" / "samples"

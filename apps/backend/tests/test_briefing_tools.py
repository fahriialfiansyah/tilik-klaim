"""The seven read-only tools — a projection of the response the reviewer already sees."""
from __future__ import annotations

import json

import pytest

from app.service.briefing.tools import TOOL_NAMES, ToolRegistry, UnknownTool
from tests.test_case_endpoints import ingest_and_screen


def _detail(api, scenario: str):
    from app.dto.cases import CaseDetailResponse

    screened = ingest_and_screen(api, scenario)
    body = api.get(f"/v1/cases/{screened['case_id']}").json()
    return CaseDetailResponse.model_validate(body)


def _ids(payload: object) -> set[str]:
    text = json.dumps(payload, default=str)
    return {token for token in text.replace('"', " ").split() if "-" in token and token[:3].isupper()}


def test_exactly_seven_tools_and_all_are_read_only(api) -> None:
    assert len(TOOL_NAMES) == 7
    registry = ToolRegistry(_detail(api, "phantom"))
    for name in TOOL_NAMES:
        arguments = registry.example_arguments(name)
        assert arguments is not None, f"{name} has no valid arguments on the phantom case"
        result = registry.call(name, arguments)
        assert result.model_config.get("frozen") is True, f"{name} returned a mutable model"


def test_unknown_tool_name_is_refused_before_dispatch(api) -> None:
    registry = ToolRegistry(_detail(api, "phantom"))
    with pytest.raises(UnknownTool):
        registry.call("write_disposition", {})
    with pytest.raises(UnknownTool):
        registry.call("submit_briefing", {})


@pytest.mark.parametrize("scenario", ("phantom", "repeat", "clone", "unbundled", "clean"))
def test_tools_cannot_see_more_than_the_screen(api, scenario: str) -> None:
    """Every identifier a tool emits already appears in the detail response."""
    detail = _detail(api, scenario)
    visible = _ids(detail.model_dump(mode="json"))
    registry = ToolRegistry(detail)
    for name in TOOL_NAMES:
        arguments = registry.example_arguments(name)
        if arguments is None:
            continue  # a quiet case has no reason to ask about
        result = registry.call(name, arguments)
        leaked = _ids(result.model_dump(mode="json")) - visible
        assert not leaked, f"{name} emitted {leaked} not on screen"


def test_the_overview_carries_no_priority_or_component_scores(api) -> None:
    registry = ToolRegistry(_detail(api, "phantom"))
    overview = registry.call("get_case_overview", {}).model_dump(mode="json")
    dumped = json.dumps(overview).lower()
    for word in ("band", "score", "priority"):
        assert word not in dumped


def test_related_bundle_redaction_survives_the_tool_surface(api) -> None:
    """The clone candidate is another participant's note. The tool gets its shape, never its text."""
    detail = _detail(api, "clone")
    registry = ToolRegistry(detail)
    peer = next(s for s in detail.sources if s.availability == "RELATED_BUNDLE")
    result = registry.call(
        "get_source_resource",
        {"resource_type": str(peer.resource_type), "resource_id": peer.resource_id},
    )
    names = {field.name for field in result.fields}
    assert "text" not in names
    assert "participant_id" not in names


def test_evidence_path_names_the_gap(api) -> None:
    detail = _detail(api, "phantom")
    registry = ToolRegistry(detail)
    path = registry.call("get_evidence_path", {"reason_code": "LINE_WITHOUT_COMPLETED_PROCEDURE"})
    assert "Procedure" in [str(t) for t in path.missing]
    assert path.cited_lines, "the phantom reason cites a line"


def test_a_missing_source_is_reported_not_invented(api) -> None:
    registry = ToolRegistry(_detail(api, "phantom"))
    result = registry.call("get_source_resource", {"resource_type": "Procedure", "resource_id": "NOPE"})
    assert str(result.availability) == "MISSING"
    assert result.fields == ()

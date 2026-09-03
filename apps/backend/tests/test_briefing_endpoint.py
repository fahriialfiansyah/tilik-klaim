"""`GET /v1/cases/{case_id}/briefing` — the eighth endpoint; the seven frozen ones are untouched."""
from __future__ import annotations

import json

import pytest
from pydantic import SecretStr

from app.config import get_settings
from app.dto.briefing import CaseBriefing
from app.service.briefing import service as briefing_service
from app.service.llm_provider import AssistantTurn, ToolCall
from tests.test_case_endpoints import ingest_and_screen


@pytest.fixture
def case_id(api) -> str:
    return ingest_and_screen(api, "phantom")["case_id"]


def _events(api, case_id: str) -> list[tuple[str, dict]]:
    out: list[tuple[str, dict]] = []
    with api.stream("GET", f"/v1/cases/{case_id}/briefing") as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        name = None
        for line in response.iter_lines():
            if line.startswith("event: "):
                name = line[len("event: "):]
            elif line.startswith("data: ") and name:
                out.append((name, json.loads(line[len("data: "):])))
                name = None
    return out


def test_an_unknown_case_is_404(api) -> None:
    response = api.get("/v1/cases/nope/briefing?stream=false")
    assert response.status_code == 404
    assert response.json()["code"] == "CASE_NOT_FOUND"


def test_disabled_briefing_is_the_template_not_an_error(api, case_id) -> None:
    assert get_settings().briefing_enabled is False, "the default must be off"
    response = api.get(f"/v1/cases/{case_id}/briefing?stream=false")
    assert response.status_code == 200
    body = CaseBriefing.model_validate(response.json())
    assert body.generated_by == "TEMPLATE"
    assert body.validation_rejected is False
    assert body.observations


def test_the_stream_emits_status_then_observations_then_done(api, case_id) -> None:
    events = _events(api, case_id)
    names = [name for name, _ in events]
    assert names[0] == "status"
    assert names[-1] == "done"
    assert "observation" in names
    assert names.index("done") > max(i for i, n in enumerate(names) if n == "observation")


def test_stream_terminal_equals_the_unstreamed_object(api, case_id) -> None:
    done = next(payload for name, payload in _events(api, case_id) if name == "done")
    flat = api.get(f"/v1/cases/{case_id}/briefing?stream=false").json()
    assert done["briefing"] == flat


def test_the_stream_asks_proxies_not_to_buffer(api, case_id) -> None:
    with api.stream("GET", f"/v1/cases/{case_id}/briefing") as response:
        assert response.headers.get("x-accel-buffering") == "no"
        assert "no-cache" in response.headers.get("cache-control", "")


def test_enabled_path_uses_the_provider_and_logs_tool_events(api, case_id, monkeypatch) -> None:
    detail = api.get(f"/v1/cases/{case_id}").json()
    ref = detail["reasons"][0]["evidence"][0]

    class Fake:
        """Reads once through a tool call, then answers the structured submission — the shape
        the gateway was measured to have."""

        def available_models(self):
            return frozenset({"Qwen3.5-9B"})

        def complete(self, messages, tools):
            if not any(m["role"] == "tool" for m in messages):
                return AssistantTurn(
                    content=None,
                    tool_calls=(ToolCall(id="1", name="list_reasons", arguments={}),),
                )
            return AssistantTurn(content="Cukup.", tool_calls=())

        def complete_structured(self, messages, schema_name, schema):
            return {
                "observations": [
                    {
                        "statement": "Baris tagihan yang dirujuk tidak punya catatan tindakan.",
                        "kind": "EVIDENCE_GAP",
                        "source_ids": [ref["resource_id"]],
                        "confidence": "STATED",
                    }
                ],
                "open_questions": [],
                "uncertainty_note": "Hanya dari bukti yang ikut terkirim.",
            }, "Qwen3.5-9B"

    settings = get_settings()
    monkeypatch.setattr(settings, "briefing_enabled", True)
    monkeypatch.setattr(settings, "vllm_api_key", SecretStr("test"))
    monkeypatch.setattr(settings, "vllm_base_url", "http://gateway.invalid:9999/v1")
    monkeypatch.setattr(settings, "llm_model_vllm", "Qwen3.5-9B")
    monkeypatch.setattr(briefing_service, "_make_provider", lambda _settings: Fake())

    events = _events(api, case_id)
    names = [name for name, _ in events]
    assert "tool" in names
    done = next(payload for name, payload in events if name == "done")["briefing"]
    assert done["generated_by"] == "LLM"
    assert done["tool_calls"] == [{"tool": "list_reasons", "arguments": {}}]


def test_the_seven_frozen_paths_are_still_exactly_seven_plus_this_one(api) -> None:
    paths = {path for path in api.app.openapi()["paths"] if path.startswith("/v1/")}
    assert "/v1/cases/{case_id}/briefing" in paths
    assert len(paths) == 8

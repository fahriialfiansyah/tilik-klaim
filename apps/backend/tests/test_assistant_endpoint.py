"""`POST /v1/assistant/answers` — the ninth endpoint; every earlier one is untouched."""
from __future__ import annotations

import json

import pytest

from app.config import get_settings
from app.dto.assistant import AssistantAnswer
from tests.test_case_endpoints import ingest_and_screen


@pytest.fixture
def case_id(api) -> str:
    return ingest_and_screen(api, "phantom")["case_id"]


def _events(api, body: dict, headers: dict | None = None) -> list[tuple[str, dict]]:
    out: list[tuple[str, dict]] = []
    with api.stream("POST", "/v1/assistant/answers", json=body, headers=headers or {}) as response:
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


def test_disabled_assistant_is_the_template_not_an_error(api, case_id) -> None:
    assert get_settings().assistant_enabled is False, "the default must be off"
    response = api.post("/v1/assistant/answers?stream=false", json={"question": "Ringkas antrean"})
    assert response.status_code == 200
    body = AssistantAnswer.model_validate(response.json())
    assert body.generated_by == "TEMPLATE"
    assert body.validation_rejected is False


def test_the_stream_emits_status_then_done(api, case_id) -> None:
    events = _events(api, {"question": "Kasus mana yang perlu dibuka dulu?"})
    names = [name for name, _ in events]
    assert names[0] == "status"
    assert names[-1] == "done"


def test_stream_terminal_equals_the_unstreamed_object(api, case_id) -> None:
    body = {"question": "Mengapa kasus ini muncul?", "scope": {"kind": "CASE", "case_id": case_id}}
    done = next(payload for name, payload in _events(api, body) if name == "done")
    flat = api.post("/v1/assistant/answers?stream=false", json=body).json()
    assert done["answer"] == flat


def test_the_stream_asks_proxies_not_to_buffer(api, case_id) -> None:
    with api.stream("POST", "/v1/assistant/answers", json={"question": "Ringkas antrean"}) as response:
        assert response.headers.get("x-accel-buffering") == "no"
        assert "no-cache" in response.headers.get("cache-control", "")


def test_a_case_scope_naming_no_known_case_is_404(api) -> None:
    response = api.post(
        "/v1/assistant/answers?stream=false",
        json={"question": "Mengapa?", "scope": {"kind": "CASE", "case_id": "nope"}},
    )
    assert response.status_code == 404
    assert response.json()["code"] == "CASE_NOT_FOUND"


@pytest.mark.parametrize(
    "body",
    [
        {"question": ""},
        {"question": "   "},
        {"question": "x" * 501},
        {"question": "q", "scope": {"kind": "CASE"}},
        {"question": "q", "scope": {"kind": "QUEUE", "case_id": "case_1"}},
        {"question": "q", "history": [{"question": "a"}] * 4},
        {"question": "q", "unexpected": True},
    ],
)
def test_malformed_requests_are_refused_before_anything_is_read(api, body) -> None:
    assert api.post("/v1/assistant/answers?stream=false", json=body).status_code == 422


def test_the_answer_follows_the_reader_language(api, case_id) -> None:
    english = api.post(
        "/v1/assistant/answers?stream=false",
        json={"question": "Why was this case raised?", "scope": {"kind": "CASE", "case_id": case_id}},
        headers={"Accept-Language": "en"},
    ).json()
    assert "deterministic rule" in english["statements"][0]["text"]
    assert english["uncertainty_note"].startswith("This answer")


def test_the_assistant_writes_nothing(api, case_id) -> None:
    """Asking about a case leaves it exactly as it was: same state, same version, same trail."""
    before = api.get(f"/v1/cases/{case_id}").json()
    audit_before = api.get(f"/v1/cases/{case_id}/audit").json()
    for question in ("Mengapa kasus ini muncul?", "Bukti apa yang belum ditemukan?"):
        api.post(
            "/v1/assistant/answers?stream=false",
            json={"question": question, "scope": {"kind": "CASE", "case_id": case_id}},
        )
    after = api.get(f"/v1/cases/{case_id}").json()
    assert (after["state"], after["case_version"]) == (before["state"], before["case_version"])
    assert api.get(f"/v1/cases/{case_id}/audit").json() == audit_before

"""The bounded runner against a scripted provider. No network anywhere in this file."""
from __future__ import annotations

import json

import pytest
from tilik_domain.versioning import EngineIdentity

from app.dto.briefing import DoneEvent, ObservationEvent, StatusEvent, ToolEvent
from app.dto.cases import CaseDetailResponse
from app.service.briefing.runner import run_briefing
from app.service.llm_provider import (
    AssistantTurn,
    LlmUnavailable,
    ToolCall,
    ToolCallsUnsupported,
)
from tests.test_case_endpoints import ingest_and_screen


@pytest.fixture
def detail(api) -> CaseDetailResponse:
    screened = ingest_and_screen(api, "phantom")
    return CaseDetailResponse.model_validate(api.get(f"/v1/cases/{screened['case_id']}").json())


class ScriptedProvider:
    """Plays reading turns in order, then answers the structured submission.

    Mirrors the shape the gateway was measured to have: tool calling for the reads, guided
    decoding for the object.
    """

    def __init__(self, *turns: AssistantTurn, payload: dict | None = None, served: str | None = None) -> None:
        self.turns = list(turns)
        self.payload = payload
        self.served = served
        self.seen: list[list[dict]] = []
        self.submitted: list[list[dict]] = []

    def available_models(self) -> frozenset[str]:
        return frozenset({"Qwen3.5-9B"})

    def complete(self, messages, tools) -> AssistantTurn:
        self.seen.append(list(messages))
        if not self.turns:
            raise LlmUnavailable("script exhausted")
        return self.turns.pop(0)

    def complete_structured(self, messages, schema_name, schema):
        self.submitted.append(list(messages))
        if self.payload is None:
            raise LlmUnavailable("submission unavailable")
        return self.payload, self.served


def _call(name: str, **arguments) -> ToolCall:
    return ToolCall(id=f"call-{name}", name=name, arguments=arguments)


DONE_READING = AssistantTurn(content="Cukup.", tool_calls=())
"""How the model says it has read enough: a turn with no tool calls."""


def _draft_payload(detail: CaseDetailResponse, **overrides) -> dict:
    cited = detail.reasons[0].evidence[0].resource_id
    draft = {
        "observations": [
            {
                # Digit-free on purpose: a number the model never read through a tool is
                # rejected by the validator — see `test_an_invented_number_falls_back…`.
                "statement": "Baris tagihan yang dirujuk tidak punya catatan tindakan yang dapat dibuka.",
                "kind": "EVIDENCE_GAP",
                "source_ids": [cited],
                "confidence": "STATED",
            }
        ],
        "open_questions": [],
        "uncertainty_note": "Disusun dari bukti yang ikut terkirim saja.",
    }
    draft.update(overrides)
    return draft


def _run(detail, provider, *, max_tool_calls=8):
    events = []
    briefing = run_briefing(
        detail, EngineIdentity(), provider, model_id="test-model",
        max_tool_calls=max_tool_calls, emit=events.append,
    )
    return briefing, events


def test_a_valid_submission_is_accepted_and_logged(detail) -> None:
    provider = ScriptedProvider(
        AssistantTurn(content=None, tool_calls=(_call("get_evidence_path", reason_code="LINE_WITHOUT_COMPLETED_PROCEDURE"),)),
        DONE_READING,
        payload=_draft_payload(detail),
    )
    briefing, events = _run(detail, provider)

    assert briefing.generated_by == "LLM"
    assert briefing.validation_rejected is False
    assert [c.tool for c in briefing.tool_calls] == ["get_evidence_path"]
    assert briefing.model_id == "test-model"
    kinds = [type(e) for e in events]
    assert kinds[0] is StatusEvent
    assert ToolEvent in kinds
    assert kinds[-1] is DoneEvent


def test_no_observation_is_streamed_before_validation(detail) -> None:
    """Unvalidated prose must never reach a client, not even as progress."""
    provider = ScriptedProvider(DONE_READING, payload=_draft_payload(detail))
    _, events = _run(detail, provider)
    validating = next(i for i, e in enumerate(events) if isinstance(e, StatusEvent) and e.phase == "VALIDATING")
    first_observation = next(i for i, e in enumerate(events) if isinstance(e, ObservationEvent))
    assert first_observation > validating


def test_an_unresolvable_reference_falls_back_to_the_template_and_says_so(detail) -> None:
    provider = ScriptedProvider(DONE_READING, payload=_draft_payload(detail, observations=[{
        "statement": "Tindakan PROC-GHOST tercatat.", "kind": "CORROBORATION",
        "source_ids": ["PROC-GHOST"], "confidence": "STATED",
    }]))
    briefing, _ = _run(detail, provider)
    assert briefing.generated_by == "TEMPLATE"
    assert briefing.validation_rejected is True
    assert "PROC-GHOST" in (briefing.rejection_reason or "")


def test_a_forbidden_term_falls_back_to_the_template(detail) -> None:
    cited = detail.reasons[0].evidence[0].resource_id
    provider = ScriptedProvider(DONE_READING, payload=_draft_payload(detail, observations=[{
        "statement": "Pola ini mengindikasikan fraud.", "kind": "EVIDENCE_GAP",
        "source_ids": [cited], "confidence": "INFERRED",
    }]))
    briefing, _ = _run(detail, provider)
    assert briefing.generated_by == "TEMPLATE"
    assert "fraud" in (briefing.rejection_reason or "")


def test_an_invented_number_falls_back_to_the_template(detail) -> None:
    cited = detail.reasons[0].evidence[0].resource_id
    provider = ScriptedProvider(DONE_READING, payload=_draft_payload(detail, observations=[{
        # A number that cannot occur in this case's tool output. "42" once did.
        "statement": "Sekitar 987654321 baris tidak berdokumen.", "kind": "COMPLETENESS",
        "source_ids": [cited], "confidence": "INFERRED",
    }]))
    briefing, _ = _run(detail, provider)
    assert briefing.generated_by == "TEMPLATE"
    assert "987654321" in (briefing.rejection_reason or "")


def test_provider_failure_falls_back_to_the_template(detail) -> None:
    briefing, events = _run(detail, ScriptedProvider())
    assert briefing.generated_by == "TEMPLATE"
    assert briefing.validation_rejected is True
    assert "script exhausted" in (briefing.rejection_reason or "")
    assert isinstance(events[-1], DoneEvent)


def test_tool_call_budget_is_enforced(detail) -> None:
    """A model that keeps reading is stopped and made to answer with what it has."""
    greedy = ScriptedProvider(
        *[AssistantTurn(content=None, tool_calls=(_call("get_timeline"),)) for _ in range(20)],
        payload=_draft_payload(detail),
    )
    briefing, _ = _run(detail, greedy, max_tool_calls=3)
    assert len(briefing.tool_calls) == 3
    assert briefing.generated_by == "LLM"


def test_an_unknown_tool_is_refused_and_reported_back_to_the_model(detail) -> None:
    provider = ScriptedProvider(
        AssistantTurn(content=None, tool_calls=(_call("write_case_note", text="x"),)),
        DONE_READING,
        payload=_draft_payload(detail),
    )
    briefing, _ = _run(detail, provider)
    # The refusal was fed back as a tool result, and the run still completed.
    fed_back = json.dumps(provider.seen[1][-1])
    assert "unknown tool" in fed_back
    assert briefing.generated_by == "LLM"


def test_a_model_that_reads_nothing_still_gets_the_evidence(detail) -> None:
    """Stopping before opening anything leaves nothing to cite, and the gates would reject it.
    The reads happen deterministically instead, so the briefing is grounded either way."""
    provider = ScriptedProvider(DONE_READING, payload=_draft_payload(detail))
    briefing, _ = _run(detail, provider)
    assert briefing.generated_by == "LLM"
    assert {c.tool for c in briefing.tool_calls} >= {"get_case_overview", "list_reasons"}


def test_a_gateway_that_cannot_produce_the_object_falls_back_to_the_template(detail) -> None:
    provider = ScriptedProvider(DONE_READING, payload=None)
    briefing, _ = _run(detail, provider)
    assert briefing.generated_by == "TEMPLATE"
    assert "submission unavailable" in (briefing.rejection_reason or "")


def test_a_malformed_object_names_the_fields_that_were_wrong(detail) -> None:
    """"2 error(s)" cost an hour of debugging once. The field names would not have."""
    provider = ScriptedProvider(DONE_READING, payload={})
    briefing, _ = _run(detail, provider)
    assert briefing.generated_by == "TEMPLATE"
    assert "observations" in (briefing.rejection_reason or "")
    assert "uncertainty_note" in (briefing.rejection_reason or "")


def test_the_model_only_ever_sees_tool_output_and_the_fixed_prompt(detail) -> None:
    """No raw bundle, no store row — the messages are the prompt plus what the tools returned."""
    provider = ScriptedProvider(
        AssistantTurn(content=None, tool_calls=(_call("get_case_overview"),)),
        DONE_READING,
        payload=_draft_payload(detail),
    )
    _run(detail, provider)
    roles = [m["role"] for m in provider.seen[-1]]
    assert roles[0] == "system"
    assert set(roles) <= {"system", "user", "assistant", "tool"}
    # And the submission sees only the fixed prompt plus what the reads returned.
    assert [m["role"] for m in provider.submitted[0]] == ["system", "user"]


class NoToolsProvider:
    """A gateway started without `--enable-auto-tool-choice`: serves the model, refuses tools."""

    def __init__(self, payload: dict | None = None, served: str = "Qwen3.5-9B") -> None:
        self.payload = payload
        self.served = served
        self.structured_calls: list[list[dict]] = []

    def complete(self, messages, tools):
        raise ToolCallsUnsupported("the gateway does not serve tool calling")

    def complete_structured(self, messages, schema_name, schema):
        self.structured_calls.append(list(messages))
        if self.payload is None:
            raise LlmUnavailable("gateway went away")
        return self.payload, self.served


def _draft(detail, **overrides):
    ref = detail.reasons[0].evidence[0].model_dump(mode="json")
    draft = {
        "observations": [
            {
                "statement": "Baris tagihan yang dirujuk tidak punya catatan tindakan.",
                "kind": "EVIDENCE_GAP",
                "source_refs": [ref],
                "reason_code": "LINE_WITHOUT_COMPLETED_PROCEDURE",
                "confidence": "STATED",
            }
        ],
        "open_questions": [],
        "uncertainty_note": "Disusun dari bukti yang ikut terkirim saja.",
    }
    draft.update(overrides)
    return draft


class TestAGatewayWithoutToolCalling:
    """vLLM only offers tool calling when started with `--enable-auto-tool-choice`.

    Without it the briefing must still work: the seven reads happen deterministically and the
    shape is enforced by the server through guided decoding. Every other guarantee is unchanged
    — same projections in, same five gates out.
    """

    def test_the_reads_still_happen_and_are_reported(self, detail) -> None:
        provider = NoToolsProvider(_draft_payload(detail))
        briefing, events = _run(detail, provider)

        assert briefing.generated_by == "LLM"
        assert briefing.validation_rejected is False
        # Every tool that had valid arguments on this case was read, and each was announced.
        assert {c.tool for c in briefing.tool_calls} >= {"get_case_overview", "list_reasons", "get_timeline"}
        assert [e.tool for e in events if isinstance(e, ToolEvent)] == [c.tool for c in briefing.tool_calls]

    def test_the_model_is_shown_only_tool_output_and_the_fixed_prompt(self, detail) -> None:
        provider = NoToolsProvider(_draft_payload(detail))
        _run(detail, provider)

        messages = provider.structured_calls[0]
        assert [m["role"] for m in messages] == ["system", "user"]
        assert "get_case_overview" in messages[1]["content"]

    def test_the_served_model_is_recorded_not_the_requested_one(self, detail) -> None:
        provider = NoToolsProvider(_draft_payload(detail), served="Qwen3.6-27B")
        briefing, _ = _run(detail, provider)
        assert briefing.model_id == "Qwen3.6-27B"

    def test_the_same_gates_apply_on_this_path(self, detail) -> None:
        provider = NoToolsProvider(
            _draft_payload(
                detail,
                observations=[
                    {
                        "statement": "Tindakan PROC-GHOST tercatat.",
                        "kind": "CORROBORATION",
                        "source_ids": ["PROC-GHOST"],
                        "confidence": "STATED",
                    }
                ],
            )
        )
        briefing, _ = _run(detail, provider)
        assert briefing.generated_by == "TEMPLATE"
        assert "PROC-GHOST" in (briefing.rejection_reason or "")

    def test_a_gateway_that_then_fails_falls_back_to_the_template(self, detail) -> None:
        briefing, events = _run(detail, NoToolsProvider(None))
        assert briefing.generated_by == "TEMPLATE"
        assert "gateway went away" in (briefing.rejection_reason or "")
        assert isinstance(events[-1], DoneEvent)

    def test_a_malformed_object_falls_back_to_the_template(self, detail) -> None:
        briefing, _ = _run(detail, NoToolsProvider({"observations": "not a list"}))
        assert briefing.generated_by == "TEMPLATE"
        assert "malformed" in (briefing.rejection_reason or "")


def test_the_schema_narrows_citable_ids_to_this_case(detail) -> None:
    """The gateway compiles the schema into a grammar, so an id that is not on this case is
    impossible to emit rather than something to catch afterwards.

    Measured against the real gateway: without this the model cited the provider token, which
    appears in tool output but is not an openable resource.
    """
    from app.service.briefing.runner import _schema_for

    schema = _schema_for(detail)
    citable = sorted({s.resource_id for s in detail.sources})
    enums = [
        definition["properties"]["source_ids"]["items"]["enum"]
        for definition in schema["$defs"].values()
        if "source_ids" in definition.get("properties", {})
    ]
    assert enums, "both draft models carry source_ids"
    for allowed in enums:
        assert allowed == citable
        assert "PRV-01" not in allowed, "a participant or provider token is not a resource"


def test_reading_stops_when_the_clock_runs_out(detail) -> None:
    """The call budget alone bounds nothing useful: eight reads against a slow gateway is
    minutes, and this panel is asked for in front of a reviewer. Observed once at over three
    minutes. Out of time means write with what has been read."""
    provider = ScriptedProvider(
        *[AssistantTurn(content=None, tool_calls=(_call("get_timeline"),)) for _ in range(20)],
        payload=_draft_payload(detail),
    )
    briefing = run_briefing(
        detail, EngineIdentity(), provider, model_id="m",
        max_tool_calls=8, emit=lambda _e: None, deadline_seconds=0,
    )
    # Never entered the read loop, so the evidence was gathered directly and it still answered.
    assert briefing.generated_by == "LLM"
    assert briefing.tool_calls

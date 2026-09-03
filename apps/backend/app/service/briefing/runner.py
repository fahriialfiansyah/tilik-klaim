"""The bounded tool-calling run: read via the seven tools, then submit one structured object.

Bounds: at most `max_tool_calls` reads, one model per run, and one terminal `submit_briefing`.
Whatever the model submits passes the validator or the whole thing falls back to the template —
nothing is trimmed, and no observation is streamed before it has been validated.
"""
from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from pydantic import Field, ValidationError
from tilik_domain.versioning import EngineIdentity

from app.dto.briefing import (
    MAX_OBSERVATIONS,
    MAX_QUESTIONS,
    BriefingEvent,
    BriefingObservation,
    BriefingPhase,
    BriefingQuestion,
    CaseBriefing,
    DoneEvent,
    GeneratedBy,
    ObservationEvent,
    StatusEvent,
    ToolCallRecord,
    ToolEvent,
)
from app.dto.cases import CaseDetailResponse
from app.dto.common import Dto, VersionStamp
from app.service.briefing.template import template_briefing
from app.service.briefing.tools import ToolArgumentError, ToolRegistry, UnknownTool
from app.service.briefing.validation import validate_briefing
from app.service.llm_provider import ChatProvider, LlmUnavailable

PROMPT_VERSION = "briefing-1"
SUBMIT_TOOL_NAME = "submit_briefing"

Emit = Callable[[BriefingEvent], None]


class DraftBriefing(Dto):
    """What the model submits. Everything else on `CaseBriefing` is filled in by this runner."""

    observations: tuple[BriefingObservation, ...] = Field(max_length=MAX_OBSERVATIONS)
    open_questions: tuple[BriefingQuestion, ...] = Field(default=(), max_length=MAX_QUESTIONS)
    uncertainty_note: str = Field(min_length=1)


SYSTEM_PROMPT = (
    "Anda menyusun ringkasan bukti untuk satu kasus tinjauan klaim, dalam bahasa Indonesia. "
    "Anda hanya boleh membaca lewat alat yang tersedia; setiap pengamatan wajib mengutip "
    "source_refs yang muncul persis di keluaran alat. Jangan menulis angka yang tidak ada di "
    "keluaran alat. Jangan menyebut fraud, kecurangan, pemalsuan, penolakan, sanksi, atau "
    "pembayaran, dan jangan menyatakan klaim bersih atau terbukti. Jangan menyarankan tindakan "
    "peninjau. Nyatakan ketidakpastian: ketiadaan catatan dalam bundel bukan bukti bahwa layanan "
    "tidak diberikan. Paling banyak lima pengamatan dan tiga pertanyaan terbuka. Setelah selesai "
    f"membaca, panggil {SUBMIT_TOOL_NAME} sekali dengan hasil terstruktur."
)


def _submit_tool() -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": SUBMIT_TOOL_NAME,
            "description": "Serahkan ringkasan terstruktur. Panggil sekali, setelah membaca.",
            "parameters": DraftBriefing.model_json_schema(),
        },
    }


def _fallback(
    detail: CaseDetailResponse,
    identity: EngineIdentity,
    reason: str,
    log: list[ToolCallRecord],
) -> CaseBriefing:
    return template_briefing(detail, identity).model_copy(
        update={"validation_rejected": True, "rejection_reason": reason, "tool_calls": tuple(log)}
    )


def _finish(briefing: CaseBriefing, emit: Emit) -> CaseBriefing:
    for observation in briefing.observations:
        emit(ObservationEvent(observation=observation))
    emit(StatusEvent(phase=BriefingPhase.DONE, detail=briefing.generated_by))
    emit(DoneEvent(briefing=briefing))
    return briefing


def _accept(
    draft: DraftBriefing,
    detail: CaseDetailResponse,
    identity: EngineIdentity,
    model_id: str,
    log: list[ToolCallRecord],
    supplied: list[str],
) -> CaseBriefing | str:
    candidate = CaseBriefing(
        case_id=detail.case_id,
        case_version=detail.case_version,
        observations=draft.observations,
        open_questions=draft.open_questions,
        uncertainty_note=draft.uncertainty_note,
        generated_by=GeneratedBy.LLM,
        model_id=model_id,
        prompt_version=PROMPT_VERSION,
        tool_calls=tuple(log),
        versions=VersionStamp(**identity.model_dump()),
    )
    verdict = validate_briefing(candidate, detail, supplied_text="\n".join(supplied))
    return candidate if verdict.accepted else (verdict.reason or "rejected")


def run_briefing(
    detail: CaseDetailResponse,
    identity: EngineIdentity,
    provider: ChatProvider,
    *,
    model_id: str,
    max_tool_calls: int,
    emit: Emit,
) -> CaseBriefing:
    registry = ToolRegistry(detail)
    tools = [*registry.definitions(), _submit_tool()]
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Susun ringkasan bukti untuk kasus {detail.case_id}."},
    ]
    supplied: list[str] = []
    log: list[ToolCallRecord] = []
    emit(StatusEvent(phase=BriefingPhase.STARTED, detail=model_id))

    # One extra step so the model can submit after spending its whole read budget.
    for _ in range(max_tool_calls + 1):
        try:
            turn = provider.complete(messages, tools)
        except LlmUnavailable as failure:
            return _finish(_fallback(detail, identity, str(failure), log), emit)

        if not turn.tool_calls:
            return _finish(_fallback(detail, identity, "model answered without calling submit_briefing", log), emit)

        messages.append(_assistant_message(turn))
        for call in turn.tool_calls:
            if call.name == SUBMIT_TOOL_NAME:
                emit(StatusEvent(phase=BriefingPhase.VALIDATING, detail="memeriksa rujukan dan istilah"))
                try:
                    draft = DraftBriefing.model_validate(call.arguments)
                except ValidationError as malformed:
                    return _finish(_fallback(detail, identity, f"malformed submission: {malformed.error_count()} error(s)", log), emit)
                outcome = _accept(draft, detail, identity, model_id, log, supplied)
                if isinstance(outcome, CaseBriefing):
                    return _finish(outcome, emit)
                return _finish(_fallback(detail, identity, outcome, log), emit)

            if len(log) >= max_tool_calls:
                return _finish(_fallback(detail, identity, "tool-call budget exhausted", log), emit)
            arguments = {k: str(v) for k, v in call.arguments.items()}
            result_text = _read(registry, call.name, call.arguments)
            supplied.append(result_text)
            log.append(ToolCallRecord(tool=call.name, arguments=arguments))
            emit(StatusEvent(phase=BriefingPhase.READING, detail=call.name))
            emit(ToolEvent(tool=call.name, arguments=arguments))
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result_text})

    return _finish(_fallback(detail, identity, "step budget exhausted", log), emit)


def _read(registry: ToolRegistry, name: str, arguments: dict[str, Any]) -> str:
    """Tool output as text — or the refusal, fed back so the model can correct itself."""
    try:
        return registry.call(name, arguments).model_dump_json()
    except UnknownTool:
        return json.dumps({"error": f"unknown tool {name!r}; only the listed read tools exist"})
    except ToolArgumentError as bad:
        return json.dumps({"error": str(bad)})


def _assistant_message(turn: Any) -> dict[str, Any]:
    return {
        "role": "assistant",
        "content": turn.content,
        "tool_calls": [
            {
                "id": call.id,
                "type": "function",
                "function": {"name": call.name, "arguments": json.dumps(call.arguments)},
            }
            for call in turn.tool_calls
        ],
    }

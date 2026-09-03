"""The bounded tool-calling run: read via the seven tools, then submit one structured object.

Bounds: at most `max_tool_calls` reads, one model per run, and one terminal `submit_briefing`.
Whatever the model submits passes the validator or the whole thing falls back to the template —
nothing is trimmed, and no observation is streamed before it has been validated.
"""
from __future__ import annotations

import json
import time
from collections.abc import Callable
from typing import Any

from pydantic import Field, ValidationError
from tilik_domain.versioning import EngineIdentity

from app.dto.briefing import (
    MAX_OBSERVATIONS,
    MAX_QUESTIONS,
    MAX_STATEMENT_CHARS,
    BriefingEvent,
    BriefingObservation,
    BriefingPhase,
    BriefingQuestion,
    CaseBriefing,
    Confidence,
    DoneEvent,
    GeneratedBy,
    ObservationEvent,
    ObservationKind,
    StatusEvent,
    ToolCallRecord,
    ToolEvent,
)
from app.dto.cases import CaseDetailResponse
from app.dto.common import Dto, EvidenceRefDto, VersionStamp
from app.service.briefing.template import template_briefing
from app.service.briefing.tools import (
    TOOL_NAMES,
    ToolArgumentError,
    ToolRegistry,
    UnknownTool,
)
from app.service.briefing.validation import validate_briefing
from app.service.llm_provider import ChatProvider, LlmUnavailable, ToolCallsUnsupported

PROMPT_VERSION = "briefing-2"

Emit = Callable[[BriefingEvent], None]


class DraftObservation(Dto):
    """One observation as the model writes it — citing ids, not whole reference objects.

    The model names `source_ids` and the runner resolves them against the case's own source
    index. That is smaller to generate, and it means a fabricated reference is not merely
    rejected afterwards but **unrepresentable**: the model can only point at resources that
    already exist on this case. It cannot invent a type or a label, because it never writes one.
    """

    statement: str = Field(min_length=1, max_length=MAX_STATEMENT_CHARS)
    kind: ObservationKind
    source_ids: tuple[str, ...] = Field(min_length=1, max_length=4)
    confidence: Confidence


class DraftQuestion(Dto):
    question: str = Field(min_length=1, max_length=MAX_STATEMENT_CHARS)
    why_it_matters: str = Field(min_length=1, max_length=MAX_STATEMENT_CHARS)
    source_ids: tuple[str, ...] = Field(min_length=1, max_length=4)


class DraftBriefing(Dto):
    """What the model submits. Everything else on `CaseBriefing` is filled in by this runner."""

    observations: tuple[DraftObservation, ...] = Field(max_length=MAX_OBSERVATIONS)
    open_questions: tuple[DraftQuestion, ...] = Field(default=(), max_length=MAX_QUESTIONS)
    # Bounded like every other field. Left unbounded it was the one place the model could run
    # long enough to exhaust the output budget and lose the whole object to truncation.
    uncertainty_note: str = Field(min_length=1, max_length=MAX_STATEMENT_CHARS)


class UnknownResource(ValueError):
    """The model cited an id that is not on this case. Gate 1, reached before the gates."""


def _resolve(ids: tuple[str, ...], detail: CaseDetailResponse) -> tuple[EvidenceRefDto, ...]:
    index = {source.resource_id: source for source in detail.sources}
    refs = []
    for resource_id in ids:
        source = index.get(resource_id)
        if source is None:
            raise UnknownResource(resource_id)
        refs.append(
            EvidenceRefDto(
                resource_type=source.resource_type,
                resource_id=source.resource_id,
                label=source.label,
            )
        )
    return tuple(refs)


def _materialise(draft: DraftBriefing, detail: CaseDetailResponse) -> tuple[
    tuple[BriefingObservation, ...], tuple[BriefingQuestion, ...]
]:
    """Turn cited ids into the reference objects the wire model carries."""
    observations = tuple(
        BriefingObservation(
            statement=item.statement,
            kind=item.kind,
            source_refs=_resolve(item.source_ids, detail),
            confidence=item.confidence,
        )
        for item in draft.observations
    )
    questions = tuple(
        BriefingQuestion(
            question=item.question,
            why_it_matters=item.why_it_matters,
            source_refs=_resolve(item.source_ids, detail),
        )
        for item in draft.open_questions
    )
    return observations, questions


RULES = (
    "Setiap pengamatan wajib mengutip source_refs yang muncul persis di keluaran alat. "
    "Jangan menulis angka yang tidak ada di keluaran alat. Jangan menyebut fraud, kecurangan, "
    "pemalsuan, penolakan, sanksi, atau pembayaran, dan jangan menyatakan klaim bersih atau "
    "terbukti. Jangan menyarankan tindakan peninjau. Nyatakan ketidakpastian: ketiadaan catatan "
    "dalam bundel bukan bukti bahwa layanan tidak diberikan. Paling banyak lima pengamatan dan "
    "tiga pertanyaan terbuka. "
    # The gateway's grammar backend does not enforce the schema's maxLength, so the limits are
    # stated here too. Without this the model wrote past the output budget and the whole object
    # was lost to truncation — full latency, no result.
    "Tulis SANGAT ringkas: satu kalimat per pengamatan, maksimal 200 karakter per teks. "
    "Boleh kurang dari lima pengamatan bila memang tidak ada yang perlu ditambahkan. "
    "Bila menyebut angka, salin persis seperti tertulis di keluaran alat — jangan mengubah "
    "format ribuan atau desimal."
)

READ_PROMPT = (
    "Anda menyusun ringkasan bukti untuk satu kasus tinjauan klaim, dalam bahasa Indonesia. "
    "Baca lewat alat yang tersedia — panggil alat yang Anda perlukan, lalu berhenti memanggil "
    f"alat ketika sudah cukup. {RULES}"
)

KIND_GUIDE = (
    "Pilih kind yang tepat untuk tiap pengamatan: EVIDENCE_GAP bila bukti yang diharapkan "
    "tidak ditemukan; CORROBORATION bila bukti yang diharapkan justru ditemukan; "
    "COUNTER_EVIDENCE bila fakta itu MELEMAHKAN alasan, termasuk penjelasan sah seperti "
    "templat bersama atau layanan bertahap; COMPARISON untuk pasangan klaim atau dokumen yang "
    "dibandingkan; TIMELINE untuk urutan waktu; COMPLETENESS untuk kelengkapan bundel. "
    "Jangan menandai semuanya EVIDENCE_GAP."
)

WRITE_PROMPT = (
    "Anda menyusun ringkasan bukti untuk satu kasus tinjauan klaim, dalam bahasa Indonesia, "
    f"hanya dari hasil pembacaan alat di bawah. {RULES} {KIND_GUIDE} "
    "Untuk source_ids, tulis resource_id apa adanya seperti yang muncul di keluaran alat "
    "(misalnya 'ENC-PH-1'), bukan objek. Jawab sebagai satu objek JSON."
)


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
    """The model that actually served is recorded, never the one that was requested."""
    try:
        observations, questions = _materialise(draft, detail)
    except UnknownResource as unknown:
        return f"unresolved reference: {unknown}"
    candidate = CaseBriefing(
        case_id=detail.case_id,
        case_version=detail.case_version,
        observations=observations,
        open_questions=questions,
        uncertainty_note=draft.uncertainty_note,
        generated_by=GeneratedBy.LLM,
        model_id=model_id,
        prompt_version=PROMPT_VERSION,
        tool_calls=tuple(log),
        versions=VersionStamp(**identity.model_dump()),
    )
    verdict = validate_briefing(candidate, detail, supplied_text="\n".join(supplied))
    return candidate if verdict.accepted else (verdict.reason or "rejected")


def _schema_for(detail: CaseDetailResponse) -> dict[str, Any]:
    """`DraftBriefing`'s schema, with `source_ids` narrowed to this case's own resources.

    The gateway compiles the schema into a grammar, so an id that is not on this case becomes
    **impossible to emit** rather than something to catch afterwards. Measured: without this the
    model cited `PRV-01`, the provider token — it appears in tool output but is not an openable
    resource, so the reviewer would have been offered a reference that goes nowhere.

    Same principle as the drawer union and the four matrix states: make the wrong state
    unrepresentable rather than merely detected.
    """
    schema = DraftBriefing.model_json_schema()
    citable = sorted({source.resource_id for source in detail.sources})
    if not citable:
        return schema
    for definition in schema.get("$defs", {}).values():
        field = definition.get("properties", {}).get("source_ids")
        if field and isinstance(field.get("items"), dict):
            field["items"] = {"type": "string", "enum": citable}
    return schema


def _describe(error: ValidationError) -> str:
    """Name the fields. "2 error(s)" cost an hour once; the field names would not have."""
    return "; ".join(
        f"{'.'.join(str(part) for part in item['loc']) or '<root>'}: {item['msg']}"
        for item in error.errors()[:4]
    )


def _gather(registry: ToolRegistry, log: list[ToolCallRecord]) -> list[str]:
    """Call every tool that has valid arguments on this case, in registry order."""
    supplied: list[str] = []
    for name in TOOL_NAMES:
        arguments = registry.example_arguments(name)
        if arguments is None:
            continue  # nothing on this case for that tool to be asked about
        supplied.append(f"{name}: {_read(registry, name, arguments)}")
        log.append(ToolCallRecord(tool=name, arguments={k: str(v) for k, v in arguments.items()}))
    return supplied


def _submit(
    detail: CaseDetailResponse,
    identity: EngineIdentity,
    provider: ChatProvider,
    model_id: str,
    supplied: list[str],
    log: list[ToolCallRecord],
    emit: Emit,
) -> CaseBriefing:
    """One guided-decoding call: the schema is enforced by the gateway, not asked for in a prompt.

    Measured, and the reason this is not a tool call: asked to *call* a tool whose parameters are
    a nested schema with `$ref`s, the model emitted the call with empty arguments every time. Ask
    it for the same object through `response_format` and the gateway holds it to the schema.
    """
    emit(StatusEvent(phase=BriefingPhase.VALIDATING, detail="memeriksa rujukan dan istilah"))
    citable = sorted({source.resource_id for source in detail.sources})
    messages = [
        {"role": "system", "content": WRITE_PROMPT},
        {
            "role": "user",
            "content": (
                f"Bukti untuk kasus {detail.case_id}, hasil pembacaan alat:\n\n"
                + "\n\n".join(supplied)
                + "\n\nsource_ids hanya boleh dipilih dari daftar ini: "
                + ", ".join(citable)
            ),
        },
    ]
    try:
        payload, served = provider.complete_structured(
            messages, "DraftBriefing", _schema_for(detail)
        )
    except LlmUnavailable as failure:
        return _fallback(detail, identity, str(failure), log)

    try:
        draft = DraftBriefing.model_validate(payload)
    except ValidationError as malformed:
        return _fallback(detail, identity, f"malformed submission: {_describe(malformed)}", log)

    outcome = _accept(draft, detail, identity, served or model_id, log, supplied)
    return outcome if isinstance(outcome, CaseBriefing) else _fallback(detail, identity, outcome, log)


def _structured_pass(
    detail: CaseDetailResponse,
    identity: EngineIdentity,
    provider: ChatProvider,
    registry: ToolRegistry,
    model_id: str,
    emit: Emit,
) -> CaseBriefing:
    """For a gateway that does not serve tool calling: read everything, then submit.

    A narrower capability, not a lesser one — the briefing sees exactly the same seven
    projections, chosen deterministically rather than by the model.
    """
    log: list[ToolCallRecord] = []
    supplied = _gather(registry, log)
    for record in log:
        emit(ToolEvent(tool=record.tool, arguments=record.arguments))
    return _submit(detail, identity, provider, model_id, supplied, log, emit)


def run_briefing(
    detail: CaseDetailResponse,
    identity: EngineIdentity,
    provider: ChatProvider,
    *,
    model_id: str,
    max_tool_calls: int,
    emit: Emit,
    deadline_seconds: float = 120.0,
) -> CaseBriefing:
    """Read through the seven tools, chosen by the model, then submit through guided decoding.

    The split is deliberate and was measured. Tool calling is what lets the model decide *what
    to look at*, and this gateway serves it well. Producing the final object is a different job:
    asked to call a tool whose parameters are a nested schema, the model emitted empty arguments
    every time, while the same object through `response_format` came back correct. So each
    mechanism does the thing it is good at.
    """
    registry = ToolRegistry(detail)
    tools = list(registry.definitions())
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": READ_PROMPT},
        {"role": "user", "content": f"Susun ringkasan bukti untuk kasus {detail.case_id}."},
    ]
    supplied: list[str] = []
    log: list[ToolCallRecord] = []
    emit(StatusEvent(phase=BriefingPhase.STARTED, detail=model_id))
    # Reading is bounded by a count *and* by the clock. The count alone bounds nothing useful:
    # eight reads against a slow gateway is minutes, and this panel is on-demand in front of a
    # reviewer. Out of time means stop reading and write with what has been read.
    reading_until = time.monotonic() + deadline_seconds

    while len(log) < max_tool_calls and time.monotonic() < reading_until:
        try:
            turn = provider.complete(messages, tools)
        except ToolCallsUnsupported:
            # The gateway serves the model but not tool calling. The reads happen here instead.
            emit(StatusEvent(phase=BriefingPhase.READING, detail="tanpa pemanggilan alat"))
            return _finish(
                _structured_pass(detail, identity, provider, registry, model_id, emit), emit
            )
        except LlmUnavailable as failure:
            return _finish(_fallback(detail, identity, str(failure), log), emit)

        if not turn.tool_calls:
            break  # the model has read enough

        messages.append(_assistant_message(turn))
        for call in turn.tool_calls:
            if len(log) >= max_tool_calls:
                break
            arguments = {k: str(v) for k, v in call.arguments.items()}
            result_text = _read(registry, call.name, call.arguments)
            supplied.append(f"{call.name}: {result_text}")
            log.append(ToolCallRecord(tool=call.name, arguments=arguments))
            emit(StatusEvent(phase=BriefingPhase.READING, detail=call.name))
            emit(ToolEvent(tool=call.name, arguments=arguments))
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result_text})

    if not supplied:
        # It never opened anything, so it has nothing to cite and the gates would reject it.
        supplied = _gather(registry, log)
        for record in log:
            emit(ToolEvent(tool=record.tool, arguments=record.arguments))

    return _finish(_submit(detail, identity, provider, model_id, supplied, log, emit), emit)


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

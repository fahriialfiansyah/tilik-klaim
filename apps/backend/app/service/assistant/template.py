"""The deterministic answers — the default, and what ships if the model is ever switched off.

Pure functions over the snapshot and the detail responses the turn was handed. Every sentence is
catalog text, a response field, or a fixed frame around one, and every statement cites what it
was read from; `08_demo_runbook.md`: "Never depend on a remote LLM" — this is the path the
offline demo runs, and the one every test pins.

Nothing here orders, ranks, or weighs. Where a question is about order, the answer points at
the queue's own order and says so.
"""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from tilik_domain.locale import Locale
from tilik_domain.reasons import CaseState, PriorityBand, RiskMode
from tilik_domain.versioning import EngineIdentity

from app.dto.assistant import (
    MAX_CASE_CARDS,
    MAX_CITATIONS_PER_STATEMENT,
    MAX_STATEMENT_CHARS,
    MAX_STATEMENTS,
    AnswerIntent,
    AnswerKind,
    AssistantAnswer,
    AssistantQuestion,
    AssistantStatement,
    CaseCard,
    Citation,
    GeneratedBy,
    RefusalTopic,
    ScopeKind,
)
from app.dto.cases import CaseDetailResponse, CaseSummary
from app.dto.common import EvidenceRefDto, ReasonDto, VersionStamp
from app.service.assistant import wording as w
from app.service.assistant.citations import (
    card,
    case_citation,
    queue_citation,
    resource_citation,
    short_id,
)
from app.service.assistant.context import AssistantContext
from app.service.assistant.intents import AWAITING_STATES, Reading
from app.service.assistant.queue_tools import rows_matching

PROMPT_VERSION = "assistant-template-1"

COMPARISON_MODES = (RiskMode.REPEAT_BILLING, RiskMode.CLONED_DOCUMENTATION)
JAKARTA = ZoneInfo("Asia/Jakarta")
MAX_REFS_PER_STATEMENT = 4
_ELLIPSIS = "…"


# ---- small pieces ---------------------------------------------------------------------------


def _clip(text: str, limit: int = MAX_STATEMENT_CHARS) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rsplit(" ", 1)[0] + _ELLIPSIS


def _say(text: str, citations: list[Citation]) -> AssistantStatement:
    unique = list({c.model_dump_json(): c for c in citations}.values())
    return AssistantStatement(text=_clip(text), citations=tuple(unique[:MAX_CITATIONS_PER_STATEMENT]))


def _number(value: float, locale: Locale) -> str:
    """`144.04` → "144,04" in Indonesian. Integers stay integers."""
    text = f"{value:g}" if value != int(value) else str(int(value))
    return text.replace(".", ",") if locale is Locale.ID else text


def _when(moment: datetime, locale: Locale) -> str:
    local = moment.astimezone(JAKARTA)
    return local.strftime("%d-%m-%Y %H.%M WIB" if locale is Locale.ID else "%Y-%m-%d %H:%M WIB")


def _openable(detail: CaseDetailResponse, refs: tuple[EvidenceRefDto, ...]) -> list[EvidenceRefDto]:
    """Only references the case's own source index can open — the rest would be dead links."""
    known = {(str(s.resource_type), s.resource_id) for s in detail.sources}
    return [ref for ref in refs if (str(ref.resource_type), ref.resource_id) in known]


def _evidence(detail: CaseDetailResponse, refs: tuple[EvidenceRefDto, ...], locale: Locale) -> list[Citation]:
    """Resource citations for `refs`, or the case itself when none of them opens."""
    openable = _openable(detail, refs)[:MAX_REFS_PER_STATEMENT]
    if not openable:
        return [case_citation(detail.case_id, locale)]
    return [resource_citation(detail.case_id, ref, locale) for ref in openable]


def _cards(positioned: tuple[tuple[int, CaseSummary], ...] | list[tuple[int, CaseSummary]]) -> tuple[CaseCard, ...]:
    return tuple(card(row, position) for position, row in list(positioned)[:MAX_CASE_CARDS])


def _cases(rows: list[CaseSummary], locale: Locale, limit: int = 5) -> list[Citation]:
    return [case_citation(row.case_id, locale) for row in rows[:limit]]


def _answer(
    request: AssistantQuestion,
    intent: AnswerIntent,
    statements: list[AssistantStatement],
    note: str,
    *,
    cards: tuple[CaseCard, ...] = (),
) -> AssistantAnswer:
    return AssistantAnswer(
        question=request.question,
        scope=request.scope,
        kind=AnswerKind.ANSWER,
        intent=intent,
        statements=tuple(statements[:MAX_STATEMENTS]),
        cases=cards,
        uncertainty_note=note,
        generated_by=GeneratedBy.TEMPLATE,
        prompt_version=PROMPT_VERSION,
        versions=VersionStamp(**EngineIdentity().model_dump()),
    )


def refusal_answer(request: AssistantQuestion, topic: RefusalTopic, locale: Locale) -> AssistantAnswer:
    """Refused before any model was called. Says what the page *can* do instead."""
    return AssistantAnswer(
        question=request.question,
        scope=request.scope,
        kind=AnswerKind.REFUSAL,
        intent=AnswerIntent.OUT_OF_SCOPE,
        refusal_topic=topic,
        notice=w.refusal(topic, locale),
        uncertainty_note=w.uncertainty_notice(locale),
        generated_by=GeneratedBy.TEMPLATE,
        prompt_version=PROMPT_VERSION,
        versions=VersionStamp(**EngineIdentity().model_dump()),
    )


def help_answer(request: AssistantQuestion, locale: Locale) -> AssistantAnswer:
    """A question the template does not recognise is answered with what it can do — not a guess."""
    return AssistantAnswer(
        question=request.question,
        scope=request.scope,
        kind=AnswerKind.HELP,
        intent=AnswerIntent.UNRECOGNISED,
        notice=w.help_notice(locale, in_case=request.scope.kind is ScopeKind.CASE),
        uncertainty_note=w.uncertainty_notice(locale),
        generated_by=GeneratedBy.TEMPLATE,
        prompt_version=PROMPT_VERSION,
        versions=VersionStamp(**EngineIdentity().model_dump()),
    )


# ---- queue scope ----------------------------------------------------------------------------


def _queue_overview(request: AssistantQuestion, ctx: AssistantContext) -> AssistantAnswer:
    loc, rows, metrics = ctx.locale, list(ctx.snapshot.rows), ctx.snapshot.metrics
    total = ctx.snapshot.total_cases
    awaiting = rows_matching(ctx.snapshot, states=AWAITING_STATES)
    awaiting_rows = [row for _, row in awaiting]
    out = [
        _say(
            w.pick(
                loc,
                f"{metrics.awaiting_review} dari {total} kasus di antrean menunggu tinjauan.",
                f"{metrics.awaiting_review} of the {total} cases in the queue are awaiting review.",
            ),
            [queue_citation(loc), *_cases(awaiting_rows, loc)],
        )
    ]
    conflicts = [row for row in rows if row.band is PriorityBand.DETERMINISTIC_CONFLICT]
    if conflicts:
        label = w.band_label(conflicts[0].band, loc)
        out.append(
            _say(
                w.pick(
                    loc,
                    f"{len(conflicts)} kasus berprioritas {label}: datanya tidak memenuhi sebuah "
                    "aturan integritas, tanpa menunjuk kesalahan pihak mana pun.",
                    f"{len(conflicts)} {'case is' if len(conflicts) == 1 else 'cases are'} in the "
                    f"{label} band: the data does not meet an integrity rule, without pointing to "
                    "fault on anyone's part.",
                ),
                _cases(conflicts, loc),
            )
        )
    mode_counts = [
        (mode, sum(1 for row in rows if mode in row.modes)) for mode in RiskMode
    ]
    present = [f"{w.mode_label(mode, loc)} ({count})" for mode, count in mode_counts if count]
    if present:
        out.append(
            _say(
                w.pick(
                    loc,
                    f"Menurut pola risiko: {w.joined(present, loc)}.",
                    f"By risk pattern: {w.joined(present, loc)}.",
                ),
                [queue_citation(loc)],
            )
        )
    if metrics.evidence_requested:
        waiting = [row for row in rows if row.state is CaseState.EVIDENCE_REQUESTED]
        out.append(
            _say(
                w.pick(
                    loc,
                    f"{metrics.evidence_requested} kasus menunggu bukti tambahan.",
                    f"{metrics.evidence_requested} awaiting additional evidence.",
                ),
                _cases(waiting, loc) or [queue_citation(loc)],
            )
        )
    if awaiting_rows:
        hours = _number(metrics.median_time_in_queue_hours, loc)
        out.append(
            _say(
                w.pick(
                    loc,
                    f"Median waktu menunggu di antrean {hours} jam.",
                    f"Median time waiting in the queue is {hours} hours.",
                ),
                [queue_citation(loc)],
            )
        )
    return _answer(
        request, AnswerIntent.QUEUE_OVERVIEW, out, w.uncertainty_queue(loc), cards=_cards(awaiting)
    )


def _where_to_start(request: AssistantQuestion, ctx: AssistantContext) -> AssistantAnswer:
    loc = ctx.locale
    awaiting = rows_matching(ctx.snapshot, states=AWAITING_STATES)
    if not awaiting:
        statement = _say(
            w.pick(
                loc,
                "Tidak ada kasus yang menunggu tinjauan di antrean saat ini.",
                "No case in the queue is awaiting review right now.",
            ),
            [queue_citation(loc)],
        )
        return _answer(request, AnswerIntent.WHERE_TO_START, [statement], w.uncertainty_queue(loc))

    position, top = awaiting[0]
    out = [
        _say(
            w.pick(
                loc,
                f"Kasus teratas yang menunggu tinjauan adalah {short_id(top.case_id)}, urutan ke-"
                f"{position} di antrean, dengan prioritas {w.band_label(top.band, loc)}.",
                f"The top case awaiting review is {short_id(top.case_id)}, position {position} "
                f"in the queue, in the {w.band_label(top.band, loc)} band.",
            ),
            [case_citation(top.case_id, loc)],
        ),
        _say(
            w.pick(
                loc,
                "Urutan ini milik antrean itu sendiri: prioritas paling mendesak lebih dulu, lalu "
                "yang paling lama menunggu. Asisten tidak menyusun urutan baru.",
                "This order is the queue's own: the most urgent band first, then the longest "
                "waiting. The assistant does not set an order of its own.",
            ),
            [queue_citation(loc)],
        ),
    ]
    detail = ctx.load_case(top.case_id)
    if detail is not None and detail.reasons:
        primary = detail.reasons[0]
        out.append(
            _say(
                w.pick(loc, f"Alasan terkuatnya: {primary.sentence}", f"Its strongest reason: {primary.sentence}"),
                _evidence(detail, primary.evidence, loc),
            )
        )
    following = awaiting[1:3]
    if following:
        names = [f"{short_id(row.case_id)} ({w.band_label(row.band, loc)})" for _, row in following]
        out.append(
            _say(
                w.pick(
                    loc,
                    f"Sesudahnya di antrean: {w.joined(names, loc)}.",
                    f"Next in the queue: {w.joined(names, loc)}.",
                ),
                [case_citation(row.case_id, loc) for _, row in following],
            )
        )
    return _answer(
        request, AnswerIntent.WHERE_TO_START, out, w.uncertainty_queue(loc), cards=_cards(awaiting[:3])
    )


def _filters_phrase(reading: Reading, loc: Locale) -> str:
    parts = []
    if reading.modes:
        names = w.joined([w.mode_label(mode, loc) for mode in reading.modes], loc)
        parts.append(w.pick(loc, f"pola {names}", f"the {names} pattern"))
    if reading.bands:
        names = w.joined([w.band_label(band, loc) for band in reading.bands], loc)
        parts.append(w.pick(loc, f"prioritas {names}", f"the {names} band"))
    if reading.states:
        if set(reading.states) == set(AWAITING_STATES):
            parts.append(w.pick(loc, "status menunggu tinjauan", "awaiting review"))
        else:
            names = w.joined([w.state_label(state, loc) for state in reading.states], loc)
            parts.append(w.pick(loc, f"status {names}", f"status {names}"))
    return w.joined(parts, loc)


def _cases_matching(request: AssistantQuestion, reading: Reading, ctx: AssistantContext) -> AssistantAnswer:
    loc = ctx.locale
    matching = rows_matching(
        ctx.snapshot, modes=reading.modes, bands=reading.bands, states=reading.states
    )
    phrase = _filters_phrase(reading, loc)
    if not matching:
        statement = _say(
            w.pick(
                loc,
                f"Tidak ada kasus dengan {phrase} di antrean saat ini.",
                f"No case in the queue currently matches {phrase}.",
            ),
            [queue_citation(loc)],
        )
        return _answer(request, AnswerIntent.CASES_MATCHING, [statement], w.uncertainty_queue(loc))

    rows = [row for _, row in matching]
    out = [
        _say(
            w.pick(
                loc,
                f"{len(rows)} kasus cocok dengan {phrase}.",
                f"{len(rows)} {'case matches' if len(rows) == 1 else 'cases match'} {phrase}.",
            ),
            [queue_citation(loc), *_cases(rows, loc)],
        )
    ]
    for position, row in matching[:3]:
        out.append(
            _say(
                w.pick(
                    loc,
                    f"Urutan ke-{position}, {short_id(row.case_id)}: {row.reason_sentence}",
                    f"Position {position}, {short_id(row.case_id)}: {row.reason_sentence}",
                ),
                [case_citation(row.case_id, loc)],
            )
        )
    return _answer(
        request, AnswerIntent.CASES_MATCHING, out, w.uncertainty_queue(loc), cards=_cards(matching)
    )


def _case_named(request: AssistantQuestion, reading: Reading, ctx: AssistantContext) -> AssistantAnswer:
    loc = ctx.locale
    prefix = reading.case_prefix or ""
    found = ctx.snapshot.matching_prefix(prefix)
    if len(found) != 1:
        positioned = [(ctx.snapshot.position_of(row.case_id) or 1, row) for row in found]
        text = (
            w.pick(
                loc,
                f"Tidak ada kasus di antrean dengan ID berawalan {prefix}.",
                f"No case in the queue has an ID starting with {prefix}.",
            )
            if not found
            else w.pick(
                loc,
                f"{len(found)} kasus memiliki ID berawalan {prefix}; sebut ID yang lebih lengkap.",
                f"{len(found)} cases have IDs starting with {prefix}; name a longer ID.",
            )
        )
        citations = [queue_citation(loc), *_cases(list(found), loc)]
        return _answer(
            request,
            AnswerIntent.CASE_OVERVIEW,
            [_say(text, citations)],
            w.uncertainty_queue(loc),
            cards=_cards(positioned),
        )

    row = found[0]
    detail = ctx.load_case(row.case_id)
    position = ctx.snapshot.position_of(row.case_id) or 1
    statements = _overview_statements(detail, loc) if detail else [
        _say(row.reason_sentence, [case_citation(row.case_id, loc)])
    ]
    return _answer(
        request,
        AnswerIntent.CASE_OVERVIEW,
        statements,
        w.uncertainty_case(loc),
        cards=(card(row, position),),
    )


# ---- case scope -----------------------------------------------------------------------------


def _quiet(detail: CaseDetailResponse, loc: Locale) -> AssistantStatement:
    return _say(
        w.pick(
            loc,
            "Tidak ada risiko teramati pada versi mesin ini, sehingga tidak ada jenis bukti yang "
            "diharapkan untuk diperiksa. Ini bukan pernyataan tentang klaimnya.",
            "No risk was observed at this engine version, so no evidence type is expected to be "
            "checked. This is not a statement about the claim.",
        ),
        [case_citation(detail.case_id, loc)],
    )


def _completeness(detail: CaseDetailResponse, loc: Locale) -> AssistantStatement:
    c = detail.evidence_completeness
    parts = [
        w.pick(
            loc,
            f"{c.supported_lines} dari {c.total_lines} baris tagihan didukung bukti.",
            f"{c.supported_lines} of {c.total_lines} claim lines are supported by evidence.",
        )
    ]
    if c.missing_reference_count:
        parts.append(
            w.pick(
                loc,
                f"{c.missing_reference_count} rujukan bukti tidak dapat diselesaikan.",
                f"{c.missing_reference_count} evidence references could not be resolved.",
            )
        )
    if not c.bundle_complete:
        parts.append(
            w.pick(
                loc,
                "Bundel dinyatakan belum lengkap, sehingga baris tanpa bukti belum dapat dinilai.",
                "The bundle is declared incomplete, so lines without evidence cannot be judged yet.",
            )
        )
    return _say(" ".join(parts), [case_citation(detail.case_id, loc)])


def _kind_of(reason: ReasonDto, loc: Locale) -> str:
    if reason.deterministic:
        return w.pick(loc, "aturan deterministik", "deterministic rule")
    return w.pick(loc, "sinyal kemiripan atau anomali", "similarity or anomaly signal")


def _overview_statements(detail: CaseDetailResponse, loc: Locale) -> list[AssistantStatement]:
    out = [
        _say(
            w.pick(
                loc,
                f"Prioritas {w.band_label(detail.band.band, loc)}. {detail.band.basis}",
                f"{w.band_label(detail.band.band, loc)} band. {detail.band.basis}",
            ),
            [case_citation(detail.case_id, loc)],
        )
    ]
    if not detail.reasons:
        out.append(_quiet(detail, loc))
    for reason in detail.reasons[:2]:
        out.append(_say(reason.sentence, _evidence(detail, reason.evidence, loc)))
    out.append(_completeness(detail, loc))
    return out


def _why_raised(detail: CaseDetailResponse, loc: Locale) -> list[AssistantStatement]:
    if not detail.reasons:
        return [_quiet(detail, loc)]
    out = [
        _say(
            f"{reason.sentence} ({w.mode_label(reason.mode, loc)}; {_kind_of(reason, loc)})",
            _evidence(detail, reason.evidence, loc),
        )
        for reason in detail.reasons[: MAX_STATEMENTS - 1]
    ]
    out.append(
        _say(
            w.pick(
                loc,
                f"Prioritas {w.band_label(detail.band.band, loc)}: {detail.band.basis}",
                f"{w.band_label(detail.band.band, loc)} band: {detail.band.basis}",
            ),
            [case_citation(detail.case_id, loc)],
        )
    )
    return out


def _missing(detail: CaseDetailResponse, loc: Locale) -> list[AssistantStatement]:
    if not detail.reasons:
        return [_quiet(detail, loc), _completeness(detail, loc)]
    out = []
    for reason in detail.reasons[: MAX_STATEMENTS - 1]:
        found_types = {ref.resource_type for ref in reason.evidence}
        expected = [w.resource_label(t, loc) for t in reason.expected_support]
        missing = [w.resource_label(t, loc) for t in reason.expected_support if t not in found_types]
        if not expected:
            continue
        if missing:
            text = w.pick(
                loc,
                f"Untuk alasan \"{reason.sentence}\" diharapkan {w.joined(expected, loc)}; yang "
                f"tidak ditemukan di bundel: {w.joined(missing, loc)}.",
                f"For the reason \"{reason.sentence}\" the expected evidence is "
                f"{w.joined(expected, loc)}; not found in the bundle: {w.joined(missing, loc)}.",
            )
        else:
            text = w.pick(
                loc,
                f"Untuk alasan \"{reason.sentence}\" semua jenis bukti yang diharapkan ditemukan.",
                f"For the reason \"{reason.sentence}\" every expected evidence type was found.",
            )
        out.append(_say(text, _evidence(detail, reason.evidence, loc)))
    out.append(_completeness(detail, loc))
    return out


def _counter(detail: CaseDetailResponse, loc: Locale) -> list[AssistantStatement]:
    out = []
    for reason in detail.reasons:
        for note in reason.counter_evidence_notes:
            out.append(_say(note.note, _evidence(detail, note.refs or reason.evidence, loc)))
    if not out:
        out.append(
            _say(
                w.pick(
                    loc,
                    "Tidak ada bukti tandingan yang tercatat untuk alasan pada kasus ini.",
                    "No counter-evidence is recorded for the reasons on this case.",
                ),
                [case_citation(detail.case_id, loc)],
            )
        )
    return out


def _timeline(detail: CaseDetailResponse, loc: Locale) -> list[AssistantStatement]:
    events = list(detail.timeline)
    if not events:
        return [
            _say(
                w.pick(loc, "Linimasa kasus ini kosong.", "This case's timeline is empty."),
                [case_citation(detail.case_id, loc)],
            )
        ]
    shown = events if len(events) <= MAX_STATEMENTS else events[: MAX_STATEMENTS - 1]
    out = [
        _say(
            f"{_when(event.occurred_at, loc)}: {event.label}",
            _evidence(detail, (event.resource,), loc) if event.resource else [case_citation(detail.case_id, loc)],
        )
        for event in shown
    ]
    remaining = len(events) - len(shown)
    if remaining:
        out.append(
            _say(
                w.pick(
                    loc,
                    f"Ada {remaining} kejadian lain di linimasa kasus ini.",
                    f"There are {remaining} more events on this case's timeline.",
                ),
                [case_citation(detail.case_id, loc)],
            )
        )
    return out


def _comparison(detail: CaseDetailResponse, loc: Locale) -> list[AssistantStatement]:
    # The same positional pairing the screen and the briefing use: comparisons travel in reason
    # order for the two comparison-shaped modes.
    comparable = [reason for reason in detail.reasons if reason.mode in COMPARISON_MODES]
    out = []
    for reason, candidate in zip(comparable, detail.comparisons, strict=False):
        same = sum(1 for f in candidate.fields if f.matches)
        out.append(
            _say(
                w.pick(
                    loc,
                    f"Dibandingkan dengan {candidate.candidate_claim_id}: {same} dari "
                    f"{len(candidate.fields)} kolom bernilai sama.",
                    f"Compared with {candidate.candidate_claim_id}: {same} of "
                    f"{len(candidate.fields)} fields hold the same value.",
                ),
                _evidence(detail, reason.evidence, loc),
            )
        )
        if candidate.template_caveat:
            out.append(_say(w.template_caveat(loc), _evidence(detail, reason.evidence, loc)))
    if not out:
        out.append(
            _say(
                w.pick(
                    loc,
                    "Kasus ini tidak punya pasangan pembanding. Perbandingan hanya dipakai untuk "
                    "pola tagihan berulang dan dokumentasi salinan.",
                    "This case has no comparison pair. Comparisons are only used for the repeat "
                    "billing and cloned documentation patterns.",
                ),
                [case_citation(detail.case_id, loc)],
            )
        )
    return out


CASE_HANDLERS = {
    AnswerIntent.CASE_OVERVIEW: _overview_statements,
    AnswerIntent.WHY_RAISED: _why_raised,
    AnswerIntent.MISSING_EVIDENCE: _missing,
    AnswerIntent.COUNTER_EVIDENCE: _counter,
    AnswerIntent.TIMELINE: _timeline,
    AnswerIntent.COMPARISON: _comparison,
}


# ---- entry point ----------------------------------------------------------------------------


def template_answer(
    request: AssistantQuestion,
    reading: Reading,
    ctx: AssistantContext,
    detail: CaseDetailResponse | None = None,
) -> AssistantAnswer:
    """`detail` is the scoped case for a CASE scope, already loaded by the caller."""
    loc = ctx.locale
    if reading.refusal_topic is not None:
        return refusal_answer(request, reading.refusal_topic, loc)

    if request.scope.kind is ScopeKind.CASE and detail is not None:
        handler = CASE_HANDLERS.get(reading.intent)
        if handler is None:
            return help_answer(request, loc)
        card_row = ctx.snapshot.row(detail.case_id)
        position = ctx.snapshot.position_of(detail.case_id)
        cards = (card(card_row, position),) if card_row and position else ()
        return _answer(request, reading.intent, handler(detail, loc), w.uncertainty_case(loc), cards=cards)

    if reading.intent is AnswerIntent.QUEUE_OVERVIEW:
        return _queue_overview(request, ctx)
    if reading.intent is AnswerIntent.WHERE_TO_START:
        return _where_to_start(request, ctx)
    if reading.intent is AnswerIntent.CASES_MATCHING:
        return _cases_matching(request, reading, ctx)
    if reading.intent is AnswerIntent.CASE_OVERVIEW and reading.case_prefix:
        return _case_named(request, reading, ctx)
    return help_answer(request, loc)

import type { BriefingPhase, ToolCallRecord } from '@/features/review/case-briefing/types'
import {
  MAX_HISTORY_ANSWER_CHARS,
  MAX_HISTORY_TURNS,
  type AssistantAnswer,
  type AssistantEvent,
  type AssistantScope,
  type Citation,
  type HistoryTurn,
} from '@/features/review/assistant/types'

/**
 * Pure state for one conversation: a turn reducer, the history a follow-up carries, and the
 * numbering of an answer's sources.
 *
 * All of it is functions of their inputs, so the page's behaviour is testable without a network,
 * the same way the briefing's `events.ts` is. Every function returns a new object; none mutates.
 */

export type TurnStatus = 'streaming' | 'done' | 'failed' | 'stopped'

export type TurnFailure = { readonly code: string | null; readonly detail: string }

export type Turn = {
  readonly id: string
  readonly question: string
  readonly scope: AssistantScope
  readonly status: TurnStatus
  readonly phase: BriefingPhase | null
  readonly phaseDetail: string | null
  readonly toolCalls: readonly ToolCallRecord[]
  readonly answer: AssistantAnswer | null
  readonly failure: TurnFailure | null
  /** True when the stream failed and the one-shot `?stream=false` answer was shown instead. */
  readonly viaFallback: boolean
}

export function newTurn(id: string, question: string, scope: AssistantScope): Turn {
  return {
    id,
    question,
    scope,
    status: 'streaming',
    phase: null,
    phaseDetail: null,
    toolCalls: [],
    answer: null,
    failure: null,
    viaFallback: false,
  }
}

/** Apply one streamed event. A turn that already ended ignores anything that arrives late. */
export function applyEvent(turn: Turn, event: AssistantEvent): Turn {
  if (turn.status !== 'streaming') {
    return turn
  }
  switch (event.name) {
    case 'status':
      return { ...turn, phase: event.data.phase, phaseDetail: event.data.detail }
    case 'tool':
      return { ...turn, toolCalls: [...turn.toolCalls, event.data] }
    case 'done':
      return withAnswer(turn, event.data.answer, false)
    case 'error':
      return withFailure(turn, { code: event.data.code, detail: event.data.detail })
  }
}

/**
 * Only a streaming turn can land. A stopped turn stays stopped and a finished one stays as it
 * was, whatever arrives afterwards — a late fallback must never overwrite what the reviewer saw.
 */
export function withAnswer(turn: Turn, answer: AssistantAnswer, viaFallback: boolean): Turn {
  if (turn.status !== 'streaming') {
    return turn
  }
  return {
    ...turn,
    status: 'done',
    phase: 'DONE',
    answer,
    // The answer's own log is the complete record; the streamed one may have missed nothing,
    // but the fallback path streamed nothing at all.
    toolCalls: answer.tool_calls,
    failure: null,
    viaFallback,
  }
}

export function withFailure(turn: Turn, failure: TurnFailure): Turn {
  return turn.status === 'streaming' ? { ...turn, status: 'failed', failure } : turn
}

export function stopped(turn: Turn): Turn {
  return turn.status === 'streaming' ? { ...turn, status: 'stopped' } : turn
}

/** The plain text of an answer, as a follow-up turn carries it and the copy button writes it. */
export function statementsText(answer: AssistantAnswer): string {
  return answer.statements.map((statement) => statement.text).join(' ')
}

/**
 * What a follow-up question carries: the last few answered turns, clipped.
 *
 * Only turns that produced an answer. A refusal or a "not recognised" carries no fact a
 * follow-up could build on, and sending it would teach the model the wrong shape of reply.
 * The server keeps no session (ADR-0007 § 3), so this is the whole of the conversation's memory
 * — and it lives in this tab only.
 */
export function historyFor(turns: readonly Turn[]): readonly HistoryTurn[] {
  return turns
    .filter((turn) => turn.status === 'done' && turn.answer?.kind === 'ANSWER')
    .slice(-MAX_HISTORY_TURNS)
    .map((turn) => ({
      question: turn.question,
      answer: statementsText(turn.answer as AssistantAnswer).slice(0, MAX_HISTORY_ANSWER_CHARS),
    }))
}

export function citationKey(citation: Citation): string {
  return [citation.kind, citation.case_id, citation.resource_type, citation.resource_id].join('|')
}

/**
 * Number an answer's sources in order of first citation, so `[2]` in the text and `2` in the
 * source list are the same thing, however many statements cite it.
 */
export function numberedSources(answer: AssistantAnswer): {
  readonly sources: readonly Citation[]
  readonly numberOf: (citation: Citation) => number
} {
  const order = new Map<string, number>()
  const sources: Citation[] = []
  for (const statement of answer.statements) {
    for (const citation of statement.citations) {
      const key = citationKey(citation)
      if (!order.has(key)) {
        order.set(key, sources.length + 1)
        sources.push(citation)
      }
    }
  }
  return { sources, numberOf: (citation) => order.get(citationKey(citation)) ?? 0 }
}

/**
 * The answer as plain text for the clipboard: statements with their source numbers, the sources,
 * and the uncertainty note. Headings are passed in, already translated.
 */
export function answerAsText(
  answer: AssistantAnswer,
  headings: { readonly sources: string; readonly uncertainty: string },
): string {
  if (answer.kind !== 'ANSWER') {
    return answer.notice ?? ''
  }
  const { sources, numberOf } = numberedSources(answer)
  const lines = answer.statements.map((statement) => {
    const marks = [...new Set(statement.citations.map(numberOf))].map((n) => `[${n}]`).join('')
    return `${statement.text} ${marks}`
  })
  const sourceLines = sources.map((source, index) => `[${index + 1}] ${source.label}`)
  return [
    ...lines,
    '',
    `${headings.sources}:`,
    ...sourceLines,
    '',
    `${headings.uncertainty}: ${answer.uncertainty_note}`,
  ].join('\n')
}

/** `case_c459a18163fd…` → `case_c459a18…` — the UI's twelve-character rule for long ids. */
export function shortId(id: string): string {
  return id.length <= 13 ? id : `${id.slice(0, 12)}…`
}

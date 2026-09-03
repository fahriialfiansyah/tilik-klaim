import type { BriefingEvent, BriefingObservation, BriefingPhase, CaseBriefing, ToolCallRecord } from '@/features/review/case-briefing/types'

/**
 * Pure state for the briefing panel: an SSE frame parser and an event reducer.
 *
 * Both are functions of their inputs and nothing else, so the panel's behaviour is testable
 * without a network — the same way the rest of this app tests selectors and stores.
 */

export type BriefingStatus = 'idle' | 'streaming' | 'done' | 'failed'

export type BriefingState = {
  readonly status: BriefingStatus
  readonly phase: BriefingPhase | null
  readonly phaseDetail: string | null
  readonly toolCalls: readonly ToolCallRecord[]
  readonly observations: readonly BriefingObservation[]
  readonly briefing: CaseBriefing | null
  readonly error: string | null
  /** True when the stream failed and the one-shot `?stream=false` fetch answered instead. */
  readonly viaFallback: boolean
}

export const IDLE_BRIEFING: BriefingState = {
  status: 'idle',
  phase: null,
  phaseDetail: null,
  toolCalls: [],
  observations: [],
  briefing: null,
  error: null,
  viaFallback: false,
}

const EVENT_NAMES = new Set(['status', 'tool', 'observation', 'done', 'error'])

/**
 * Split a text buffer into complete SSE frames. A frame is `event: x\ndata: {...}\n\n`; whatever
 * follows the last blank line is returned as `rest` for the next chunk to complete.
 */
export function parseSseChunk(buffer: string): {
  readonly events: readonly BriefingEvent[]
  readonly rest: string
} {
  const frames = buffer.split('\n\n')
  const rest = frames.pop() ?? ''
  const events: BriefingEvent[] = []
  for (const frame of frames) {
    const parsed = parseFrame(frame)
    if (parsed) {
      events.push(parsed)
    }
  }
  return { events, rest }
}

function parseFrame(frame: string): BriefingEvent | null {
  let name: string | null = null
  const dataLines: string[] = []
  for (const line of frame.split('\n')) {
    if (line.startsWith('event: ')) {
      name = line.slice('event: '.length).trim()
    } else if (line.startsWith('data: ')) {
      dataLines.push(line.slice('data: '.length))
    }
  }
  if (!name || !EVENT_NAMES.has(name) || dataLines.length === 0) {
    return null
  }
  try {
    return { name, data: JSON.parse(dataLines.join('\n')) } as BriefingEvent
  } catch {
    // A frame the server did not finish writing is not an event; the next chunk completes it.
    return null
  }
}

/** Apply one event. Always returns a new object; never mutates `state`. */
export function applyEvent(state: BriefingState, event: BriefingEvent): BriefingState {
  switch (event.name) {
    case 'status':
      return { ...state, status: 'streaming', phase: event.data.phase, phaseDetail: event.data.detail }
    case 'tool':
      return { ...state, status: 'streaming', toolCalls: [...state.toolCalls, event.data] }
    case 'observation':
      return { ...state, observations: [...state.observations, event.data.observation] }
    case 'done':
      return {
        ...state,
        status: 'done',
        phase: 'DONE',
        briefing: event.data.briefing,
        observations: event.data.briefing.observations,
        toolCalls: event.data.briefing.tool_calls,
      }
    case 'error':
      return { ...state, status: 'failed', error: event.data.detail }
  }
}

/** The one-shot answer, shaped as if it had streamed. */
export function fromBriefing(briefing: CaseBriefing, viaFallback: boolean): BriefingState {
  return {
    ...IDLE_BRIEFING,
    status: 'done',
    phase: 'DONE',
    briefing,
    observations: briefing.observations,
    toolCalls: briefing.tool_calls,
    viaFallback,
  }
}

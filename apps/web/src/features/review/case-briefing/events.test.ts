import { describe, expect, test } from 'vitest'

import {
  IDLE_BRIEFING,
  applyEvent,
  fromBriefing,
  parseSseChunk,
} from '@/features/review/case-briefing/events'
import type { BriefingObservation, CaseBriefing } from '@/features/review/case-briefing/types'

const OBSERVATION: BriefingObservation = {
  statement: 'Baris tagihan yang dirujuk tidak punya catatan tindakan.',
  kind: 'EVIDENCE_GAP',
  source_refs: [{ resource_type: 'ClaimLine', resource_id: 'LN-P2', label: 'x' }],
  reason_code: 'LINE_WITHOUT_COMPLETED_PROCEDURE',
  confidence: 'STATED',
}

const BRIEFING: CaseBriefing = {
  case_id: 'case_1',
  case_version: 1,
  observations: [OBSERVATION],
  open_questions: [],
  uncertainty_note: 'Hanya dari bukti yang ikut terkirim.',
  generated_by: 'TEMPLATE',
  model_id: null,
  prompt_version: 'template-1',
  validation_rejected: false,
  rejection_reason: null,
  tool_calls: [],
  versions: { schema_version: '0.1.0', ruleset_version: '0.1.0', engine_version: '0.1.0', dataset_version: 'unset' },
}

describe('parseSseChunk', () => {
  test('parses complete frames and keeps the unfinished tail', () => {
    const buffer =
      'event: status\ndata: {"phase":"STARTED","detail":"x"}\n\n' +
      'event: tool\ndata: {"tool":"list_reasons","arguments":{}}\n\n' +
      'event: done\ndata: {"brief'
    const { events, rest } = parseSseChunk(buffer)
    expect(events.map((e) => e.name)).toEqual(['status', 'tool'])
    expect(rest).toBe('event: done\ndata: {"brief')
  })

  test('ignores frames with names it does not know', () => {
    const { events } = parseSseChunk('event: heartbeat\ndata: {}\n\n')
    expect(events).toEqual([])
  })
})

describe('applyEvent', () => {
  test('records tool calls in arrival order without mutating the previous state', () => {
    const first = applyEvent(IDLE_BRIEFING, { name: 'tool', data: { tool: 'list_reasons', arguments: {} } })
    const second = applyEvent(first, { name: 'tool', data: { tool: 'get_timeline', arguments: {} } })
    expect(second.toolCalls.map((c) => c.tool)).toEqual(['list_reasons', 'get_timeline'])
    expect(first.toolCalls).toHaveLength(1)
    expect(IDLE_BRIEFING.toolCalls).toHaveLength(0)
  })

  test('a status event moves to streaming and names the phase', () => {
    const next = applyEvent(IDLE_BRIEFING, { name: 'status', data: { phase: 'VALIDATING', detail: '' } })
    expect(next.status).toBe('streaming')
    expect(next.phase).toBe('VALIDATING')
  })

  test('done carries the whole briefing and settles observations from it', () => {
    const next = applyEvent(IDLE_BRIEFING, { name: 'done', data: { briefing: BRIEFING } })
    expect(next.status).toBe('done')
    expect(next.briefing).toBe(BRIEFING)
    expect(next.observations).toEqual([OBSERVATION])
  })

  test('error marks the run failed with the server detail', () => {
    const next = applyEvent(IDLE_BRIEFING, { name: 'error', data: { code: 'X', detail: 'rusak' } })
    expect(next.status).toBe('failed')
    expect(next.error).toBe('rusak')
  })
})

describe('fromBriefing', () => {
  test('flags a one-shot answer as loaded without a stream', () => {
    expect(fromBriefing(BRIEFING, true).viaFallback).toBe(true)
    expect(fromBriefing(BRIEFING, true).status).toBe('done')
  })
})

import { describe, expect, test } from 'vitest'

import {
  answerAsText,
  applyEvent,
  historyFor,
  newTurn,
  numberedSources,
  shortId,
  stopped,
  withAnswer,
  withFailure,
  type Turn,
} from '@/features/review/assistant/conversation'
import {
  ANSWER,
  CASE_CITATION,
  QUEUE_CITATION,
  REFUSAL,
  RESOURCE_CITATION,
} from '@/features/review/assistant/test-fixtures'
import { MAX_HISTORY_ANSWER_CHARS, QUEUE_SCOPE } from '@/features/review/assistant/types'

function streaming(): Turn {
  return newTurn('t1', ANSWER.question, QUEUE_SCOPE)
}

describe('a turn follows its stream and never mutates', () => {
  test('status and tool events build the reading log in order', () => {
    const start = streaming()
    const read = applyEvent(
      applyEvent(start, { name: 'status', data: { phase: 'READING', detail: 'find_cases' } }),
      { name: 'tool', data: { tool: 'find_cases', arguments: { band: 'DETERMINISTIC_CONFLICT' } } },
    )
    expect(read.phase).toBe('READING')
    expect(read.toolCalls.map((call) => call.tool)).toEqual(['find_cases'])
    expect(start.toolCalls).toEqual([])
  })

  test('done carries the answer and takes its own reading log as the record', () => {
    const answer = { ...ANSWER, tool_calls: [{ tool: 'get_queue_overview', arguments: {} }] }
    const done = applyEvent(streaming(), { name: 'done', data: { answer } })
    expect(done.status).toBe('done')
    expect(done.answer).toBe(answer)
    expect(done.toolCalls).toEqual(answer.tool_calls)
  })

  test('an error event fails the turn with the server code kept', () => {
    const failed = applyEvent(streaming(), {
      name: 'error',
      data: { code: 'ASSISTANT_UNAVAILABLE', detail: 'TimeoutError' },
    })
    expect(failed.status).toBe('failed')
    expect(failed.failure).toEqual({ code: 'ASSISTANT_UNAVAILABLE', detail: 'TimeoutError' })
  })

  test('anything arriving after the turn ended is ignored', () => {
    const halted = stopped(streaming())
    expect(applyEvent(halted, { name: 'done', data: { answer: ANSWER } })).toBe(halted)
    const done = withAnswer(streaming(), ANSWER, false)
    expect(stopped(done)).toBe(done)
  })

  test('a stopped turn is never overwritten by a late fallback or failure', () => {
    const halted = stopped(streaming())
    expect(withAnswer(halted, ANSWER, true)).toBe(halted)
    expect(withFailure(halted, { code: null, detail: 'late' })).toBe(halted)
  })

  test('the one-shot fallback is flagged as such', () => {
    expect(withAnswer(streaming(), ANSWER, true).viaFallback).toBe(true)
    expect(withFailure(streaming(), { code: null, detail: 'x' }).status).toBe('failed')
  })
})

describe('a follow-up carries only what answered, and not much of it', () => {
  test('only answered turns, the last three, clipped', () => {
    const long = { ...ANSWER, statements: [{ text: 'x'.repeat(2000), citations: [CASE_CITATION] }] }
    const turns = [
      withAnswer(newTurn('a', 'q1', QUEUE_SCOPE), ANSWER, false),
      withAnswer(newTurn('b', 'q2', QUEUE_SCOPE), REFUSAL, false),
      withAnswer(newTurn('c', 'q3', QUEUE_SCOPE), ANSWER, false),
      withFailure(newTurn('d', 'q4', QUEUE_SCOPE), { code: null, detail: 'down' }),
      withAnswer(newTurn('e', 'q5', QUEUE_SCOPE), ANSWER, false),
      withAnswer(newTurn('f', 'q6', QUEUE_SCOPE), long, false),
    ]
    const history = historyFor(turns)
    expect(history.map((turn) => turn.question)).toEqual(['q3', 'q5', 'q6'])
    expect(history[2].answer).toHaveLength(MAX_HISTORY_ANSWER_CHARS)
  })
})

describe('sources are numbered once, in order of first citation', () => {
  test('a source cited twice keeps its first number', () => {
    const { sources, numberOf } = numberedSources(ANSWER)
    expect(sources).toEqual([CASE_CITATION, QUEUE_CITATION, RESOURCE_CITATION])
    expect(numberOf(CASE_CITATION)).toBe(1)
    expect(numberOf(RESOURCE_CITATION)).toBe(3)
  })

  test('the clipboard text carries the numbers, the sources, and the uncertainty', () => {
    const text = answerAsText(ANSWER, { sources: 'Sumber', uncertainty: 'Ketidakpastian' })
    expect(text).toContain('Urutan ini milik antrean itu sendiri. [2]')
    expect(text).toContain('selesai. [3][1]')
    expect(text).toContain('[3] baris tagihan LN-P2')
    expect(text).toContain('Ketidakpastian: Jawaban ini hanya membaca antrean.')
  })

  test('a refusal copies as its notice', () => {
    expect(answerAsText(REFUSAL, { sources: 'S', uncertainty: 'U' })).toBe(REFUSAL.notice)
  })
})

test('long ids keep twelve characters and an ellipsis', () => {
  expect(shortId('case_c459a18163fd48f29717db37dac71a2d')).toBe('case_c459a18…')
  expect(shortId('LN-P2')).toBe('LN-P2')
})

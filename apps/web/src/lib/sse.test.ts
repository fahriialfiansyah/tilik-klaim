import { describe, expect, test } from 'vitest'

import { parseSseFrames } from '@/lib/sse'

const NAMES = new Set(['status', 'done'])

describe('the shared SSE frame parser', () => {
  test('splits complete frames and keeps the unfinished remainder', () => {
    const buffer =
      'event: status\ndata: {"phase":"STARTED"}\n\n' +
      'event: done\ndata: {"ok":true}\n\n' +
      'event: status\ndata: {"pha'
    const { frames, rest } = parseSseFrames(buffer, NAMES)
    expect(frames).toEqual([
      { name: 'status', data: { phase: 'STARTED' } },
      { name: 'done', data: { ok: true } },
    ])
    expect(rest).toBe('event: status\ndata: {"pha')
  })

  test('drops names it was not asked for, frames without data, and broken JSON', () => {
    const buffer =
      'event: observation\ndata: {"x":1}\n\n' +
      'event: status\n\n' +
      'event: status\ndata: {broken\n\n'
    expect(parseSseFrames(buffer, NAMES).frames).toEqual([])
  })

  test('reads frames written with CRLF line endings', () => {
    const buffer = 'event: done\r\ndata: {"ok":true}\r\n\r\n'
    expect(parseSseFrames(buffer, NAMES).frames).toEqual([{ name: 'done', data: { ok: true } }])
  })
})

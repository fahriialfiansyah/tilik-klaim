import { act, renderHook, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest'

import { ANSWER } from '@/features/review/assistant/test-fixtures'
import { useAssistantStore } from '@/features/review/assistant/store'
import { QUEUE_SCOPE } from '@/features/review/assistant/types'
import { useAskAssistant } from '@/features/review/assistant/useAskAssistant'
import { useSession } from '@/features/auth/useSession'
import { ApiError, NetworkError } from '@/lib/http'

const api = vi.hoisted(() => ({ streamAnswer: vi.fn(), fetchAnswer: vi.fn() }))
vi.mock('@/features/review/assistant/api', () => api)

beforeEach(() => {
  useAssistantStore.getState().reset()
  api.streamAnswer.mockReset()
  api.fetchAnswer.mockReset()
})

afterEach(() => {
  useAssistantStore.getState().reset()
})

describe('asking, and what happens when the stream does not cooperate', () => {
  test('a streamed answer lands on its turn', async () => {
    api.streamAnswer.mockImplementation(async (_body, onEvent) => {
      onEvent({ name: 'status', data: { phase: 'STARTED', detail: 'template' } })
      onEvent({ name: 'done', data: { answer: ANSWER } })
    })
    const { result } = renderHook(() => useAskAssistant())
    act(() => result.current.ask('Kasus mana yang perlu dibuka dulu?', QUEUE_SCOPE))

    await waitFor(() => expect(result.current.turns[0]?.status).toBe('done'))
    expect(result.current.turns[0].answer).toEqual(ANSWER)
    expect(result.current.turns[0].viaFallback).toBe(false)
    expect(api.fetchAnswer).not.toHaveBeenCalled()
  })

  test('a broken stream is asked once more, unstreamed, and flagged', async () => {
    api.streamAnswer.mockRejectedValue(new NetworkError(new Error('reset')))
    api.fetchAnswer.mockResolvedValue(ANSWER)
    const { result } = renderHook(() => useAskAssistant())
    act(() => result.current.ask('q', QUEUE_SCOPE))

    await waitFor(() => expect(result.current.turns[0]?.status).toBe('done'))
    expect(result.current.turns[0].viaFallback).toBe(true)
  })

  test('a stream that closes without a terminal event falls back too', async () => {
    api.streamAnswer.mockResolvedValue(undefined)
    api.fetchAnswer.mockResolvedValue(ANSWER)
    const { result } = renderHook(() => useAskAssistant())
    act(() => result.current.ask('q', QUEUE_SCOPE))

    await waitFor(() => expect(result.current.turns[0]?.viaFallback).toBe(true))
  })

  test('a refusal from the server is not retried — it would be refused the same way', async () => {
    api.streamAnswer.mockRejectedValue(
      new ApiError(403, { code: 'CASE_ACCESS_FORBIDDEN', detail: 'no' }),
    )
    const { result } = renderHook(() => useAskAssistant())
    act(() => result.current.ask('q', QUEUE_SCOPE))

    await waitFor(() => expect(result.current.turns[0]?.status).toBe('failed'))
    expect(result.current.turns[0].failure?.code).toBe('CASE_ACCESS_FORBIDDEN')
    expect(api.fetchAnswer).not.toHaveBeenCalled()
  })

  test('a follow-up sends the earlier answered turn as history', async () => {
    api.streamAnswer.mockImplementation(async (_body, onEvent) => {
      onEvent({ name: 'done', data: { answer: ANSWER } })
    })
    const { result } = renderHook(() => useAskAssistant())
    act(() => result.current.ask('pertama', QUEUE_SCOPE))
    await waitFor(() => expect(result.current.turns[0]?.status).toBe('done'))
    act(() => result.current.ask('kedua', QUEUE_SCOPE))

    await waitFor(() => expect(api.streamAnswer).toHaveBeenCalledTimes(2))
    const body = api.streamAnswer.mock.calls[1][0]
    expect(body.history).toEqual([
      { question: 'pertama', answer: ANSWER.statements.map((s) => s.text).join(' ') },
    ])
  })

  test('stop ends the turn and aborts the request', async () => {
    let signal: AbortSignal | undefined
    api.streamAnswer.mockImplementation(
      (_body, _onEvent, abort: AbortSignal) =>
        new Promise((_resolve, reject) => {
          signal = abort
          abort.addEventListener('abort', () => reject(new DOMException('aborted', 'AbortError')))
        }),
    )
    const { result } = renderHook(() => useAskAssistant())
    act(() => result.current.ask('q', QUEUE_SCOPE))
    expect(result.current.isBusy).toBe(true)
    act(() => result.current.stop())

    expect(result.current.turns[0].status).toBe('stopped')
    expect(signal?.aborted).toBe(true)
    expect(api.fetchAnswer).not.toHaveBeenCalled()
  })

  test('signing in as somebody else clears the conversation', async () => {
    api.streamAnswer.mockImplementation(async (_body, onEvent) => {
      onEvent({ name: 'done', data: { answer: ANSWER } })
    })
    const { result } = renderHook(() => useAskAssistant())
    act(() => result.current.ask('q', QUEUE_SCOPE))
    await waitFor(() => expect(result.current.turns).toHaveLength(1))

    act(() => useSession.setState({ user: null }))
    act(() =>
      useSession.setState({
        user: {
          user_id: 'usr_other',
          staff_code: 'PTG-02',
          full_name: 'Petugas Lain',
          email: 'lain@rsud-demo.example',
          role: 'reviewer',
          is_active: true,
          last_signed_in_at: null,
        },
      }),
    )
    expect(result.current.turns).toEqual([])
  })
})

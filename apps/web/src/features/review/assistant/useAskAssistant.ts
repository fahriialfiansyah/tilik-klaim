import { useCallback } from 'react'

import { fetchAnswer, streamAnswer } from '@/features/review/assistant/api'
import {
  applyEvent,
  historyFor,
  stopped,
  withAnswer,
  withFailure,
  type Turn,
} from '@/features/review/assistant/conversation'
import { useAssistantStore } from '@/features/review/assistant/store'
import type { AssistantQuestion, AssistantScope } from '@/features/review/assistant/types'
import { ApiError } from '@/lib/http'

/**
 * In-flight streams, by turn. Module-level rather than in a ref, so a reviewer who opens a cited
 * case mid-answer comes back to a finished answer instead of a turn that was silently dropped
 * when the page unmounted.
 */
const controllers = new Map<string, AbortController>()

// Starting a new conversation abandons whatever the old one was still reading.
useAssistantStore.subscribe((state, previous) => {
  if (state.turns.length === 0 && previous.turns.length > 0) {
    controllers.forEach((controller) => controller.abort())
    controllers.clear()
  }
})

function failureOf(cause: unknown): { code: string | null; detail: string } {
  if (cause instanceof ApiError) {
    // FastAPI's own 422 is not the project envelope: no `code`, and `detail` is a list.
    return { code: cause.code ?? `HTTP_${cause.status}`, detail: String(cause.message) }
  }
  return { code: null, detail: cause instanceof Error ? cause.message : String(cause) }
}

/**
 * Ask a question and follow the answer as it is prepared.
 *
 * If the stream breaks before its terminal event, the one-shot `?stream=false` answer is fetched
 * once and shown, flagged as such: a dev proxy that buffers SSE must not turn into a failed turn.
 * A **refusal** from the server — a role that may not ask, a case that no longer exists — is not
 * retried: asking the same thing unstreamed would be refused the same way.
 */
export function useAskAssistant(): {
  readonly turns: readonly Turn[]
  readonly isBusy: boolean
  readonly ask: (question: string, scope: AssistantScope) => void
  readonly stop: () => void
  readonly reset: () => void
} {
  const turns = useAssistantStore((state) => state.turns)
  const start = useAssistantStore((state) => state.start)
  const update = useAssistantStore((state) => state.update)
  const reset = useAssistantStore((state) => state.reset)
  const isBusy = turns.some((turn) => turn.status === 'streaming')

  const ask = useCallback(
    (question: string, scope: AssistantScope) => {
      const body: AssistantQuestion = {
        question,
        scope,
        history: historyFor(useAssistantStore.getState().turns),
      }
      const id = start(question, scope)
      const controller = new AbortController()
      controllers.set(id, controller)
      let finished = false

      // Shares the stream's abort signal, so Stop and "new conversation" cancel it too.
      const fallback = async () => {
        try {
          const answer = await fetchAnswer(body, controller.signal)
          update(id, (turn) => withAnswer(turn, answer, true))
        } catch (cause) {
          if (!controller.signal.aborted) {
            update(id, (turn) => withFailure(turn, failureOf(cause)))
          }
        }
      }

      streamAnswer(
        body,
        (event) => {
          if (controller.signal.aborted) {
            return
          }
          if (event.name === 'done' || event.name === 'error') {
            finished = true
          }
          update(id, (turn) => applyEvent(turn, event))
        },
        controller.signal,
      )
        .then(() => {
          if (!finished && !controller.signal.aborted) {
            // The stream closed without a terminal event — a proxy cut it. Ask once, plainly.
            return fallback()
          }
          return undefined
        })
        .catch((cause: unknown) => {
          // Aborted on purpose, or the answer already landed and only the closing of the
          // connection failed: either way there is nothing to recover.
          if (controller.signal.aborted || finished) {
            return undefined
          }
          // A 4xx is the server saying no; a 5xx is a proxy or a crash, worth one plain retry.
          if (cause instanceof ApiError && cause.status < 500) {
            update(id, (turn) => withFailure(turn, failureOf(cause)))
            return undefined
          }
          return fallback()
        })
        .finally(() => controllers.delete(id))
    },
    [start, update],
  )

  const stop = useCallback(() => {
    for (const turn of useAssistantStore.getState().turns) {
      if (turn.status === 'streaming') {
        controllers.get(turn.id)?.abort()
        controllers.delete(turn.id)
        update(turn.id, stopped)
      }
    }
  }, [update])

  return { turns, isBusy, ask, stop, reset }
}

import { useCallback, useEffect, useRef, useState } from 'react'

import { fetchBriefing, streamBriefing } from '@/features/review/case-briefing/api'
import {
  IDLE_BRIEFING,
  applyEvent,
  fromBriefing,
  type BriefingState,
} from '@/features/review/case-briefing/events'

/**
 * Server state for the briefing panel. **Never starts on its own** — the reviewer asks for a
 * briefing; the screen does not volunteer one, so the reasons are always read first.
 *
 * If the stream fails before it finishes, the one-shot `?stream=false` answer is fetched and
 * shown, flagged as such: a dev proxy that buffers SSE must not turn into a blank panel.
 */
export function useCaseBriefing(caseId: string): {
  readonly state: BriefingState
  readonly start: () => void
  readonly reset: () => void
} {
  const [state, setState] = useState<BriefingState>(IDLE_BRIEFING)
  const controller = useRef<AbortController | null>(null)

  const reset = useCallback(() => {
    controller.current?.abort()
    controller.current = null
    setState(IDLE_BRIEFING)
  }, [])

  // A different case is a different briefing; whatever was streaming is stale.
  useEffect(() => reset, [caseId, reset])

  const start = useCallback(() => {
    controller.current?.abort()
    const abort = new AbortController()
    controller.current = abort
    setState({ ...IDLE_BRIEFING, status: 'streaming' })

    let finished = false
    streamBriefing(
      caseId,
      (event) => {
        if (abort.signal.aborted) {
          return
        }
        if (event.name === 'done' || event.name === 'error') {
          finished = true
        }
        setState((current) => applyEvent(current, event))
      },
      abort.signal,
    )
      .then(() => {
        if (!finished && !abort.signal.aborted) {
          // The stream closed without a terminal event — a proxy cut it. Ask once, plainly.
          return fetchBriefing(caseId).then((briefing) => setState(fromBriefing(briefing, true)))
        }
        return undefined
      })
      .catch(async (cause: unknown) => {
        if (abort.signal.aborted) {
          return
        }
        try {
          setState(fromBriefing(await fetchBriefing(caseId), true))
        } catch {
          const message = cause instanceof Error ? cause.message : 'Layanan tidak merespons.'
          setState((current) => ({ ...current, status: 'failed', error: message }))
        }
      })
  }, [caseId])

  return { state, start, reset }
}

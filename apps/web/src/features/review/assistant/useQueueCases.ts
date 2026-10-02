import { useCallback, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'

import type { CaseQueueResponse, CaseSummary } from '@/features/review/shared/types'
import { request } from '@/lib/http'

/** The queue endpoint's own ceiling — the assistant's snapshot is never larger either. */
const PAGE_SIZE = 200

export type PositionedCase = { readonly position: number; readonly row: CaseSummary }

export type QueueCasesState =
  | { readonly status: 'loading'; readonly cases: readonly PositionedCase[] }
  | { readonly status: 'ready'; readonly cases: readonly PositionedCase[] }
  | { readonly status: 'failed'; readonly cases: readonly PositionedCase[] }

/**
 * The queue, in its own order, for the scope picker and the scope card.
 *
 * Read from `GET /v1/cases` exactly as the queue page reads it, so the position shown beside a
 * case here is the position the reviewer sees there. Re-read when the language changes: the
 * reason sentence on each row is catalog text and arrives in the reader's language.
 */
export function useQueueCases(): QueueCasesState & { readonly reload: () => void } {
  const { i18n } = useTranslation()
  const [state, setState] = useState<QueueCasesState>({ status: 'loading', cases: [] })
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let isCurrent = true
    setState((previous) => ({ status: 'loading', cases: previous.cases }))
    request<CaseQueueResponse>(`/cases?page_size=${PAGE_SIZE}`)
      .then((response) => {
        if (isCurrent) {
          setState({
            status: 'ready',
            cases: response.items.map((row, index) => ({ position: index + 1, row })),
          })
        }
      })
      .catch(() => {
        if (isCurrent) {
          setState((previous) => ({ status: 'failed', cases: previous.cases }))
        }
      })
    return () => {
      isCurrent = false
    }
  }, [i18n.language, attempt])

  const reload = useCallback(() => setAttempt((count) => count + 1), [])
  return { ...state, reload }
}

import { useCallback, useEffect, useState } from 'react'

import { fetchQueue } from '@/features/review/queue/api'
import { useQueueStore } from '@/features/review/queue/store'
import type { CaseQueueResponse } from '@/features/review/shared/types'
import { useEngineVersion } from '@/modules/engine-version/useEngineVersion'

export type QueueStatus = 'loading' | 'ready' | 'failed'

type QueueResult = {
  readonly status: QueueStatus
  readonly data: CaseQueueResponse | null
  readonly error: Error | null
  readonly reload: () => void
}

/**
 * Server state for the queue, held here rather than in the Zustand store — mixing the two
 * would let a stale response outlive the filters that produced it.
 *
 * Refetching is manual, per `brief/03_ANTREAN_REVIEW.md` § 9.2: no polling. Rows shifting under
 * a reviewer who is mid-read is a distraction, not a feature.
 */
export function useQueue(): QueueResult {
  const filters = useQueueStore((state) => state.filters)
  const sort = useQueueStore((state) => state.sort)
  const order = useQueueStore((state) => state.order)
  const page = useQueueStore((state) => state.page)
  const setVersions = useEngineVersion((state) => state.setVersions)

  const [status, setStatus] = useState<QueueStatus>('loading')
  const [data, setData] = useState<CaseQueueResponse | null>(null)
  const [error, setError] = useState<Error | null>(null)
  const [reloadToken, setReloadToken] = useState(0)

  const reload = useCallback(() => setReloadToken((token) => token + 1), [])

  useEffect(() => {
    let active = true
    setStatus('loading')
    setError(null)

    fetchQueue({ filters, sort, order, page })
      .then((response) => {
        if (!active) {
          return
        }
        setData(response)
        // Every screening response carries the engine stamp; the header (G3) renders it.
        setVersions(response.metrics.versions)
        setStatus('ready')
      })
      .catch((cause: unknown) => {
        if (!active) {
          return
        }
        setError(cause instanceof Error ? cause : new Error(String(cause)))
        setStatus('failed')
      })

    // Guards against a slow earlier request landing after a newer one and showing the
    // reviewer results for filters they have already changed.
    return () => {
      active = false
    }
  }, [filters, sort, order, page, reloadToken, setVersions])

  return { status, data, error, reload }
}

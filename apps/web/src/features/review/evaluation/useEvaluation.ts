import { useCallback, useEffect, useState } from 'react'

import { fetchEvaluation } from '@/features/review/evaluation/api'
import type { EvaluationResponse } from '@/features/review/evaluation/types'
import { ApiError } from '@/lib/http'

/**
 * `absent` is not `failed`.
 *
 * "No evaluation has been run yet" and "the service is down" both produce an empty page, and
 * `sprint/00-app-spec.md` § 6 rule 4 makes conflating them a defect: the first needs the command
 * to run, the second needs a retry. Collapsing them leaves a reader with no way to tell which.
 */
export type EvaluationStatus = 'loading' | 'ready' | 'absent' | 'failed'

const RUN_NOT_FOUND = 'EVALUATION_RUN_NOT_FOUND'

type EvaluationResult = {
  readonly status: EvaluationStatus
  readonly data: EvaluationResponse | null
  readonly error: Error | null
  readonly reload: () => void
}

export function useEvaluation(runId?: string): EvaluationResult {
  const [status, setStatus] = useState<EvaluationStatus>('loading')
  const [data, setData] = useState<EvaluationResponse | null>(null)
  const [error, setError] = useState<Error | null>(null)
  const [reloadToken, setReloadToken] = useState(0)

  const reload = useCallback(() => setReloadToken((token) => token + 1), [])

  useEffect(() => {
    let active = true
    setStatus('loading')
    setError(null)

    fetchEvaluation(runId)
      .then((response) => {
        if (!active) {
          return
        }
        setData(response)
        setStatus('ready')
      })
      .catch((cause: unknown) => {
        if (!active) {
          return
        }
        setData(null)
        if (cause instanceof ApiError && cause.code === RUN_NOT_FOUND) {
          setStatus('absent')
          return
        }
        setError(cause instanceof Error ? cause : new Error(String(cause)))
        setStatus('failed')
      })

    return () => {
      active = false
    }
  }, [runId, reloadToken])

  return { status, data, error, reload }
}

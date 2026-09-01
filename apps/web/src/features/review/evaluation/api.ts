import type { EvaluationResponse } from '@/features/review/evaluation/types'
import { request } from '@/lib/http'

/** Reserved run id resolving to the most recent completed run. */
export const LATEST_RUN = 'latest'

/**
 * Fetch one evaluation run.
 *
 * A 404 here is a **state**, not a failure: it means nobody has run the offline evaluation yet,
 * and the page shows the command rather than an error. `useEvaluation` makes that distinction;
 * this function only fetches.
 */
export async function fetchEvaluation(runId: string = LATEST_RUN): Promise<EvaluationResponse> {
  return request<EvaluationResponse>(`/evaluations/${encodeURIComponent(runId)}`)
}

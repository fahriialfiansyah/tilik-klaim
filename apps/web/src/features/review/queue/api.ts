import type { QueueFilters, SortKey, SortOrder } from '@/features/review/queue/store'
import type { CaseQueueResponse } from '@/features/review/shared/types'
import { query, request } from '@/lib/http'

export const PAGE_SIZE = 25

type FetchQueueArgs = {
  readonly filters: QueueFilters
  readonly sort: SortKey
  readonly order: SortOrder
  readonly page: number
}

/**
 * Fetch one page of the queue.
 *
 * **Every** filter, the search term included, is a query parameter rather than a client-side
 * array operation. The response is already paginated, so narrowing or re-ordering it here would
 * act on one page and silently ignore every match on the others.
 *
 * Search was briefly done in the client, and it stranded cases: a term matching only a case on
 * page 2 emptied page 1, and the empty state that followed offered nothing but "clear the
 * filters" — no way to page forward carrying the term. The match is on the pseudonymous case
 * identifier alone; there is no name or national-ID field anywhere in this system to search by.
 */
export async function fetchQueue({
  filters,
  sort,
  order,
  page,
}: FetchQueueArgs): Promise<CaseQueueResponse> {
  return request<CaseQueueResponse>(
    `/cases${query({
      state: filters.state,
      band: filters.band,
      mode: filters.mode,
      created_after: filters.created_after,
      created_before: filters.created_before,
      search: filters.search?.trim(),
      sort,
      order,
      page,
      page_size: PAGE_SIZE,
    })}`,
  )
}

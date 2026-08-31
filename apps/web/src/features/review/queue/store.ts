import { create } from 'zustand'

import type { CaseState, PriorityBand, RiskMode } from '@/features/review/shared/types'

export const SORT_KEYS = ['band', 'age', 'amount', 'evidence'] as const
export type SortKey = (typeof SORT_KEYS)[number]
export type SortOrder = 'asc' | 'desc'

export type QueueFilters = {
  readonly state?: CaseState
  readonly band?: PriorityBand
  readonly mode?: RiskMode
  readonly created_after?: string
  readonly created_before?: string
  readonly search?: string
}

type QueueStore = {
  readonly filters: QueueFilters
  readonly sort: SortKey
  readonly order: SortOrder
  readonly page: number
  readonly setFilter: <K extends keyof QueueFilters>(key: K, value: QueueFilters[K]) => void
  readonly clearFilter: (key: keyof QueueFilters) => void
  readonly clearAllFilters: () => void
  readonly toggleSort: (key: SortKey) => void
  readonly setPage: (page: number) => void
}

/**
 * Filters, sort, and page for the review queue.
 *
 * This lives in a module-level store rather than component state for one reason from
 * `brief/03_ANTREAN_REVIEW.md` § 4.2: returning from a case must land the reviewer back on the
 * same filters and order they left. Losing them on every round trip is what makes a review tool
 * exhausting to use, and the brief calls that out specifically.
 *
 * Server data is **not** kept here. Only the reviewer's own choices are client state.
 */
export const useQueueStore = create<QueueStore>((set) => ({
  filters: {},
  sort: 'band',
  order: 'desc',
  page: 1,

  setFilter: (key, value) =>
    set((current) => ({ filters: { ...current.filters, [key]: value }, page: 1 })),

  clearFilter: (key) =>
    set((current) => {
      const { [key]: _removed, ...rest } = current.filters
      return { filters: rest, page: 1 }
    }),

  clearAllFilters: () => set({ filters: {}, page: 1 }),

  toggleSort: (key) =>
    set((current) => ({
      sort: key,
      // Re-clicking the active column flips it; moving to a new column starts descending.
      // The band column is excluded: the server ignores direction for it, so flipping the
      // stored order would announce a sort direction the rows do not actually have.
      order:
        key === 'band'
          ? 'desc'
          : current.sort === key && current.order === 'desc'
            ? 'asc'
            : 'desc',
      page: 1,
    })),

  setPage: (page) => set({ page }),
}))

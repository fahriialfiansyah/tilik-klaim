import { X } from 'lucide-react'
import { useTranslation } from 'react-i18next'

import { type QueueFilters, useQueueStore } from '@/features/review/queue/store'
import { useBandLabel, useModeLabel, useStateLabel } from '@/features/review/shared/labels'
import { CASE_STATES, PRIORITY_BANDS, RISK_MODES } from '@/features/review/shared/types'

const SELECT_CLASS =
  'rounded-md border border-line bg-card px-[9px] py-[7px] text-body text-ink outline-none focus-visible:border-brand'

/**
 * Filters, search, and the removable chips for whatever is active (widgets 6–8).
 *
 * Native `<select>` is used rather than a Radix Select: the platform control is already fully
 * keyboard-operable and screen-reader correct, and there is no custom option rendering here that
 * would justify rebuilding that behaviour.
 */
export function QueueFilterBar({ shownCount }: { readonly shownCount: number }) {
  const { t } = useTranslation('queue')
  const stateLabel = useStateLabel()
  const bandLabel = useBandLabel()
  const modeLabel = useModeLabel()
  const filters = useQueueStore((state) => state.filters)
  const setFilter = useQueueStore((state) => state.setFilter)
  const clearFilter = useQueueStore((state) => state.clearFilter)
  const clearAllFilters = useQueueStore((state) => state.clearAllFilters)

  const active = Object.entries(filters).filter(([, value]) => value !== undefined && value !== '')

  /**
   * The words on an active-filter chip.
   *
   * Defined inside the component rather than beside it because it needs the same label hooks
   * the selects use — one lookup table for the enum, so a chip can never name a status the
   * dropdown above it spells differently.
   */
  function chipText(key: keyof QueueFilters, value: string): string {
    if (key === 'state') {
      return t('filter.chip.state', { value: stateLabel(value as never) })
    }
    if (key === 'band') {
      return t('filter.chip.band', { value: bandLabel(value as never) })
    }
    if (key === 'mode') {
      return t('filter.chip.mode', { value: modeLabel(value as never) })
    }
    if (key === 'created_after') {
      return t('filter.chip.created_after', { value })
    }
    if (key === 'created_before') {
      return t('filter.chip.created_before', { value })
    }
    return t('filter.chip.search', { value })
  }

  return (
    <>
      <div className="flex flex-wrap items-center gap-2 border-b border-line px-[14px] py-3">
        <select
          id="queue-filter-state"
          name="state"
          aria-label={t('filter.stateLabel')}
          className={SELECT_CLASS}
          value={filters.state ?? ''}
          onChange={(event) =>
            setFilter('state', (event.target.value || undefined) as QueueFilters['state'])
          }
        >
          <option value="">{t('filter.stateAll')}</option>
          {CASE_STATES.map((state) => (
            <option key={state} value={state}>
              {stateLabel(state)}
            </option>
          ))}
        </select>

        <select
          id="queue-filter-mode"
          name="mode"
          aria-label={t('filter.modeLabel')}
          className={SELECT_CLASS}
          value={filters.mode ?? ''}
          onChange={(event) =>
            setFilter('mode', (event.target.value || undefined) as QueueFilters['mode'])
          }
        >
          <option value="">{t('filter.modeAll')}</option>
          {RISK_MODES.map((mode) => (
            <option key={mode} value={mode}>
              {modeLabel(mode)}
            </option>
          ))}
        </select>

        <select
          id="queue-filter-band"
          name="band"
          aria-label={t('filter.bandLabel')}
          className={SELECT_CLASS}
          value={filters.band ?? ''}
          onChange={(event) =>
            setFilter('band', (event.target.value || undefined) as QueueFilters['band'])
          }
        >
          <option value="">{t('filter.bandAll')}</option>
          {PRIORITY_BANDS.map((band) => (
            <option key={band} value={band}>
              {bandLabel(band)}
            </option>
          ))}
        </select>

        <label className="flex items-center gap-2 text-meta text-ink-3">
          {t('filter.since')}
          <input
            type="date"
            id="queue-filter-since"
            name="created_after"
            aria-label={t('filter.sinceLabel')}
            className={SELECT_CLASS}
            value={filters.created_after?.slice(0, 10) ?? ''}
            onChange={(event) =>
              setFilter(
                'created_after',
                event.target.value ? `${event.target.value}T00:00:00Z` : undefined,
              )
            }
          />
        </label>

        <label className="flex items-center gap-2 text-meta text-ink-3">
          {t('filter.until')}
          <input
            type="date"
            id="queue-filter-until"
            name="created_before"
            aria-label={t('filter.untilLabel')}
            className={SELECT_CLASS}
            value={filters.created_before?.slice(0, 10) ?? ''}
            onChange={(event) =>
              setFilter(
                'created_before',
                // End of the chosen day, so "until 5 Sep" includes cases screened that day.
                event.target.value ? `${event.target.value}T23:59:59Z` : undefined,
              )
            }
          />
        </label>

        {/*
          Search accepts a pseudonymous case identifier only. There is no name or national-ID
          field in this system to search by — those columns do not exist, by design.
        */}
        <input
          type="search"
          id="queue-search"
          name="search"
          aria-label={t('filter.search')}
          placeholder={t('filter.search')}
          className={`${SELECT_CLASS} min-w-[210px] flex-1`}
          value={filters.search ?? ''}
          onChange={(event) => setFilter('search', event.target.value || undefined)}
        />
      </div>

      <div className="flex flex-wrap items-center gap-2 border-b border-line bg-sunk px-[14px] py-[10px]">
        <span className="font-mono text-micro font-semibold tracking-label text-ink-3">
          {t('filter.activeHeading')}
        </span>

        {active.map(([key, value]) => (
          <button
            key={key}
            type="button"
            onClick={() => clearFilter(key as keyof QueueFilters)}
            className="flex items-center gap-[7px] rounded-full border border-brand-line bg-brand-soft py-[3px] pr-[6px] pl-[10px] text-small text-ink transition-colors hover:border-brand"
          >
            {chipText(key as keyof QueueFilters, String(value))}
            <span
              aria-hidden
              className="flex size-[15px] items-center justify-center rounded-full bg-card text-ink-2"
            >
              <X className="size-[9px]" />
            </span>
            <span className="sr-only">{t('filter.removeChip')}</span>
          </button>
        ))}

        {active.length === 0 ? (
          <span className="text-small text-ink-3">{t('filter.none')}</span>
        ) : (
          <button
            type="button"
            onClick={clearAllFilters}
            className="px-2 py-[3px] text-small text-brand underline"
          >
            {t('filter.clearAll')}
          </button>
        )}

        <span data-numeric className="ml-auto font-mono text-meta text-ink-2">
          {t('filter.shown', { count: shownCount })}
        </span>
      </div>
    </>
  )
}

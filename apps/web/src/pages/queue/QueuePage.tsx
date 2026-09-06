import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'

import { PageHeader, PageShell } from '@/components/layouts/PageShell'
import { Button } from '@/components/ui/button'
import { QueueFilterBar } from '@/features/review/queue/components/QueueFilterBar'
import { QueueMetricCards } from '@/features/review/queue/components/QueueMetricCards'
import {
  QueueEmpty,
  QueueFailed,
  QueueFilteredEmpty,
  QueueLoading,
} from '@/features/review/queue/components/QueuePlaceholders'
import { QueueTable } from '@/features/review/queue/components/QueueTable'
import { useQueueStore } from '@/features/review/queue/store'
import { useQueue } from '@/features/review/queue/useQueue'
import { useBandLabel, useModeLabel, useStateLabel } from '@/features/review/shared/labels'

/** Page 1 — Review queue (`/`). Widgets 1-11 per sprint/00-app-spec.md § 3. */
export function QueuePage() {
  const { t } = useTranslation('queue')
  const navigate = useNavigate()
  const stateLabel = useStateLabel()
  const bandLabel = useBandLabel()
  const modeLabel = useModeLabel()
  const { status, data, error, reload } = useQueue()
  const filters = useQueueStore((state) => state.filters)
  const page = useQueueStore((state) => state.page)
  const setPage = useQueueStore((state) => state.setPage)
  const clearAllFilters = useQueueStore((state) => state.clearAllFilters)

  // Named in the reader's language, and phrased as a list rather than assembled from a verb
  // plus a value — "status Tersaring" and "status Screened" agree on shape by accident, and the
  // next language would not.
  const activeFilterLabels = [
    filters.state && t('filter.summary.state', { value: stateLabel(filters.state) }),
    filters.band && t('filter.summary.band', { value: bandLabel(filters.band) }),
    filters.mode && t('filter.summary.mode', { value: modeLabel(filters.mode) }),
    filters.created_after &&
      t('filter.summary.created_after', { value: filters.created_after.slice(0, 10) }),
    filters.created_before &&
      t('filter.summary.created_before', { value: filters.created_before.slice(0, 10) }),
    filters.search && t('filter.summary.search', { value: filters.search }),
  ].filter((label): label is string => Boolean(label))

  const rows = data?.items ?? []
  const pageInfo = data?.page

  return (
    <PageShell width="wide">
      <PageHeader
        eyebrow={t('page.eyebrow')}
        title={t('page.title')}
        lede={t('page.lede')}
        action={
          <Button size="lg" onClick={() => navigate('/ingest')}>
            {t('page.ingestAction')}
          </Button>
        }
      />

      {data ? <QueueMetricCards metrics={data.metrics} /> : null}

      <div className="overflow-hidden rounded-lg border border-line bg-card shadow-panel">
        <QueueFilterBar shownCount={rows.length} />

        {status === 'loading' ? <QueueLoading /> : null}

        {status === 'failed' ? <QueueFailed error={error} onRetry={reload} /> : null}

        {/*
          Two different empty screens, chosen by whether a filter is responsible. Showing the
          "no cases yet" invitation while a filter is quietly hiding everything would send a
          reviewer to re-ingest data that is already there.
        */}
        {status === 'ready' && rows.length === 0 && activeFilterLabels.length > 0 ? (
          <QueueFilteredEmpty activeFilters={activeFilterLabels} onClear={clearAllFilters} />
        ) : null}

        {status === 'ready' && rows.length === 0 && activeFilterLabels.length === 0 ? (
          <QueueEmpty />
        ) : null}

        {status === 'ready' && rows.length > 0 ? (
          <>
            <QueueTable rows={rows} />
            {pageInfo ? (
              <div className="flex items-center justify-between gap-4 bg-sunk px-[14px] py-[11px]">
                <span data-numeric className="font-mono text-meta text-ink-3">
                  {t('pagination.summary', {
                    page: pageInfo.page,
                    total: Math.max(1, pageInfo.total_pages),
                    count: pageInfo.total_items,
                  })}
                </span>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={pageInfo.page <= 1}
                    onClick={() => setPage(page - 1)}
                  >
                    {t('pagination.previous')}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={pageInfo.page >= pageInfo.total_pages}
                    onClick={() => setPage(page + 1)}
                  >
                    {t('pagination.next')}
                  </Button>
                </div>
              </div>
            ) : null}
          </>
        ) : null}
      </div>

      <p className="mt-4 max-w-[760px] text-small text-ink-3">{t('page.footnote')}</p>
    </PageShell>
  )
}

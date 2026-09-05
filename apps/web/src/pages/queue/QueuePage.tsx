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
import { BAND_LABELS, MODE_LABELS, STATE_LABELS } from '@/features/review/shared/labels'

/** Page 1 — Review queue (`/`). Widgets 1-11 per sprint/00-app-spec.md § 3. */
export function QueuePage() {
  const navigate = useNavigate()
  const { status, data, error, reload } = useQueue()
  const filters = useQueueStore((state) => state.filters)
  const page = useQueueStore((state) => state.page)
  const setPage = useQueueStore((state) => state.setPage)
  const clearAllFilters = useQueueStore((state) => state.clearAllFilters)

  const activeFilterLabels = [
    filters.state && `status ${STATE_LABELS[filters.state]}`,
    filters.band && `pita ${BAND_LABELS[filters.band]}`,
    filters.mode && `mode ${MODE_LABELS[filters.mode]}`,
    filters.created_after && `sejak ${filters.created_after.slice(0, 10)}`,
    filters.created_before && `sampai ${filters.created_before.slice(0, 10)}`,
    filters.search && `pencarian "${filters.search}"`,
  ].filter((label): label is string => Boolean(label))

  const rows = data?.items ?? []
  const pageInfo = data?.page

  return (
    <PageShell width="wide">
      <PageHeader
        eyebrow="DAFTAR KERJA · TERURUT PITA PRIORITAS"
        title="Antrean Review"
        lede="Setiap baris dibuka dengan kalimat alasannya. Skor, pita, dan nominal berada di kanannya — bukan sebaliknya."
        action={
          <Button size="lg" onClick={() => navigate('/ingest')}>
            Masukkan bundel baru
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
          "belum ada kasus" invitation while a filter is quietly hiding everything would send a
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
                  Halaman {pageInfo.page} dari {Math.max(1, pageInfo.total_pages)} ·{' '}
                  {pageInfo.total_items} kasus
                </span>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={pageInfo.page <= 1}
                    onClick={() => setPage(page - 1)}
                  >
                    Sebelumnya
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={pageInfo.page >= pageInfo.total_pages}
                    onClick={() => setPage(page + 1)}
                  >
                    Berikutnya
                  </Button>
                </div>
              </div>
            ) : null}
          </>
        ) : null}
      </div>

      <p className="mt-4 max-w-[760px] text-small text-ink-3">
        Halaman ini sengaja tidak memuat grafik agregat, peringkat fasilitas, atau angka rupiah
        &ldquo;diselamatkan&rdquo;. Kasus tanpa sinyal tidak pernah dilabeli bersih — hanya
        &ldquo;tidak ada risiko teramati&rdquo;.
      </p>
    </PageShell>
  )
}

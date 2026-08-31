import { useNavigate } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { useQueueStore } from '@/features/review/queue/store'
import { formatHours } from '@/features/review/shared/format'
import type { QueueMetrics } from '@/features/review/shared/types'
import { copyStamp } from '@/modules/engine-version/useEngineVersion'
import { cn } from '@/lib/utils'

/**
 * The five operational metrics (widgets 1–5). Exactly five, and every one of them changes what
 * a reviewer does next.
 *
 * `docs/canonical/01_product_decision.md` § Main dashboard principles rules out the alternatives
 * explicitly: no "fraud saved", no rupiah "recovered", no provider league tables, no national
 * projections. Those are not omissions to fill in later.
 */
export function QueueMetricCards({ metrics }: { readonly metrics: QueueMetrics }) {
  const navigate = useNavigate()
  const setFilter = useQueueStore((state) => state.setFilter)
  const clearAllFilters = useQueueStore((state) => state.clearAllFilters)

  const cards = [
    {
      key: 'awaiting',
      label: 'Kasus menunggu ditinjau',
      value: metrics.awaiting_review,
      unit: 'kasus',
      accent: 'bg-brand',
      hint: 'Sudah tersaring, belum diambil siapa pun',
      onClick: () => {
        clearAllFilters()
        setFilter('state', 'SCREENED')
      },
    },
    {
      key: 'conflicts',
      label: 'Konflik deterministik prioritas tinggi',
      value: metrics.deterministic_conflicts,
      unit: 'kasus',
      accent: 'bg-band-conflict',
      hint: 'Aturan integritas dilanggar secara pasti',
      onClick: () => {
        clearAllFilters()
        setFilter('band', 'DETERMINISTIC_CONFLICT')
      },
    },
    {
      key: 'evidence',
      label: 'Kasus menunggu bukti tambahan',
      value: metrics.evidence_requested,
      unit: 'kasus',
      accent: 'bg-band-context',
      hint: 'Kelengkapan sudah diminta ke fasilitas',
      onClick: () => {
        clearAllFilters()
        setFilter('state', 'EVIDENCE_REQUESTED')
      },
    },
    {
      key: 'median',
      label: 'Waktu tengah dalam antrean',
      value: formatHours(metrics.median_time_in_queue_hours),
      unit: 'jam',
      accent: 'bg-ink-3',
      hint: 'Sebaran lama tunggu, bukan target kinerja',
      onClick: clearAllFilters,
    },
  ] as const

  return (
    <div className="mb-[14px] grid grid-cols-[repeat(auto-fit,minmax(186px,1fr))] gap-3">
      {cards.map((card) => (
        <button
          key={card.key}
          type="button"
          onClick={card.onClick}
          title="Terapkan saringan ini"
          className="relative flex flex-col gap-[2px] overflow-hidden rounded-lg border border-line bg-card px-4 pt-[15px] pb-[14px] text-left shadow-panel transition-colors hover:border-line-strong"
        >
          <span aria-hidden className={cn('absolute inset-y-0 left-0 w-[3px]', card.accent)} />
          <span className="min-h-[31px] text-small leading-[1.3] text-ink-2">{card.label}</span>
          <span className="flex items-baseline gap-[6px]">
            <span
              data-numeric
              className="text-[32px] font-semibold leading-none tracking-[-0.035em]"
            >
              {card.value}
            </span>
            <span className="font-mono text-micro text-ink-3">{card.unit}</span>
          </span>
          <span className="mt-[3px] text-meta text-ink-3">{card.hint}</span>
        </button>
      ))}

      {/* Widget 5 — engine and dataset stamp (G3). The way through to /evaluation. */}
      <div className="flex flex-col gap-2 rounded-lg border border-line bg-card px-4 py-[15px] shadow-panel">
        <span className="font-mono text-micro font-semibold tracking-label text-ink-3">
          VERSI MESIN &amp; DATA
        </span>
        <span data-numeric className="font-mono text-small leading-[1.55]">
          aturan v{metrics.versions.ruleset_version}
          <br />
          model v{metrics.versions.engine_version}
          <br />
          data {metrics.versions.dataset_version}
        </span>
        <div className="mt-auto flex gap-[6px]">
          <Button
            variant="outline"
            size="sm"
            className="flex-1 px-0"
            onClick={() => void copyStamp(metrics.versions)}
          >
            Salin
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="flex-1 px-0"
            onClick={() => navigate('/evaluation')}
          >
            Evaluasi
          </Button>
        </div>
      </div>
    </div>
  )
}

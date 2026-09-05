import type { CSSProperties } from 'react'
import { useNavigate } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { useQueueStore } from '@/features/review/queue/store'
import { formatHours } from '@/features/review/shared/format'
import type { QueueMetrics } from '@/features/review/shared/types'
import { copyStamp } from '@/modules/engine-version/useEngineVersion'
import { useCountUp } from '@/modules/motion/useCountUp'
import { cn } from '@/lib/utils'

/**
 * Dua tingkat, dan pembedanya datang dari produk — bukan dari selera tata letak.
 *
 * Tiga kartu pertama adalah **hitungan yang mengubah apa yang dikerjakan berikutnya**;
 * menekannya menyaring antrean. Kartu keempat adalah sebaran waktu tunggu, dan katanya
 * sendiri "bukan target kinerja". Menggambar keempatnya dengan bobot yang sama membuat
 * angka yang sengaja bukan target terbaca seperti target.
 */
const TIER_CLASSES = {
  action: 'bg-card shadow-panel',
  reference: 'bg-sunk',
} as const

const NUMERAL_CLASSES = {
  action: 'text-[32px]',
  reference: 'text-[22px]',
} as const

type Tier = keyof typeof TIER_CLASSES

type MetricCardModel = {
  readonly key: string
  readonly label: string
  /** Hitungan yang boleh berdetak naik. `null` untuk nilai yang sudah diformat jadi teks. */
  readonly count: number | null
  readonly text?: string
  readonly unit: string
  readonly accent: string
  readonly border?: string
  readonly hint: string
  readonly tier: Tier
  readonly onClick: () => void
}

/**
 * Satu kartu. Komponen tersendiri karena `useCountUp` adalah hook: dipanggil di dalam
 * `map` ia akan melanggar aturan hook, dan angka masing-masing kartu memang butuh
 * penghitungnya sendiri.
 */
function MetricCard({ card, index }: { readonly card: MetricCardModel; readonly index: number }) {
  const counted = useCountUp(card.count ?? 0)

  return (
    <button
      type="button"
      onClick={card.onClick}
      title="Terapkan saringan ini"
      style={{ '--tk-index': index } as CSSProperties}
      className={cn(
        'tk-enter relative flex flex-col gap-[2px] overflow-hidden rounded-lg border px-4 pt-[15px] pb-[14px] text-left',
        'transition-colors duration-[var(--motion-fast)] hover:border-line-strong',
        TIER_CLASSES[card.tier],
        card.border ?? 'border-line',
      )}
    >
      {/*
        Rel warna pita. Statis, dan itu disengaja: design/DESIGN.md memberi merah satu
        tugas — menandai konflik deterministik — dan rel merah yang berdenyut berhenti
        menandai konflik lalu mulai terbaca sebagai alarm. Yang bergerak di kartu ini
        hanya angkanya, yang warnanya netral.
      */}
      <span aria-hidden className={cn('absolute inset-y-0 left-0 w-[3px]', card.accent)} />
      <span className="min-h-[31px] text-small leading-[1.3] text-ink-2">{card.label}</span>
      <span className="flex items-baseline gap-[6px]">
        <span
          data-numeric
          className={cn('font-semibold leading-none tracking-[-0.035em]', NUMERAL_CLASSES[card.tier])}
        >
          {card.count === null ? card.text : counted}
        </span>
        <span className="font-mono text-micro text-ink-3">{card.unit}</span>
      </span>
      <span className="mt-[3px] text-meta text-ink-3">{card.hint}</span>
    </button>
  )
}

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

  const cards: readonly MetricCardModel[] = [
    {
      key: 'awaiting',
      label: 'Kasus menunggu ditinjau',
      count: metrics.awaiting_review,
      unit: 'kasus',
      accent: 'bg-brand',
      hint: 'Sudah tersaring, belum diambil siapa pun',
      tier: 'action',
      onClick: () => {
        clearAllFilters()
        setFilter('state', 'SCREENED')
      },
    },
    {
      key: 'conflicts',
      label: 'Konflik deterministik prioritas tinggi',
      count: metrics.deterministic_conflicts,
      unit: 'kasus',
      accent: 'bg-band-conflict',
      // Satu-satunya kartu yang batasnya diwarnai: aturan integritas yang dilanggar
      // secara pasti adalah yang paling menentukan urutan kerja hari itu.
      border: 'border-band-conflict-line',
      hint: 'Aturan integritas dilanggar secara pasti',
      tier: 'action',
      onClick: () => {
        clearAllFilters()
        setFilter('band', 'DETERMINISTIC_CONFLICT')
      },
    },
    {
      key: 'evidence',
      label: 'Kasus menunggu bukti tambahan',
      count: metrics.evidence_requested,
      unit: 'kasus',
      accent: 'bg-band-context',
      hint: 'Kelengkapan sudah diminta ke fasilitas',
      tier: 'action',
      onClick: () => {
        clearAllFilters()
        setFilter('state', 'EVIDENCE_REQUESTED')
      },
    },
    {
      key: 'median',
      label: 'Waktu tengah dalam antrean',
      count: null,
      text: formatHours(metrics.median_time_in_queue_hours),
      unit: 'jam',
      accent: 'bg-ink-3',
      hint: 'Sebaran lama tunggu, bukan target kinerja',
      tier: 'reference',
      onClick: clearAllFilters,
    },
  ]

  return (
    <div className="mb-[14px] grid grid-cols-[repeat(auto-fit,minmax(186px,1fr))] gap-3">
      {cards.map((card, index) => (
        <MetricCard key={card.key} card={card} index={index} />
      ))}

      {/* Widget 5 — engine and dataset stamp (G3). The way through to /evaluation. */}
      <div
        style={{ '--tk-index': cards.length } as CSSProperties}
        className="tk-enter flex flex-col gap-2 rounded-lg border border-line bg-sunk px-4 py-[15px]"
      >
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

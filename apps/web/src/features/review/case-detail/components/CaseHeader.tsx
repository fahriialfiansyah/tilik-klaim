import { useState } from 'react'

import { ACTION_LABELS, componentLabel } from '@/features/review/case-detail/labels'
import type { CaseDetail, DispositionAction } from '@/features/review/case-detail/types'
import { DISPOSITION_ACTIONS } from '@/features/review/case-detail/types'
import { BAND_RAIL, BandBadge } from '@/features/review/shared/components/BandBadge'
import { formatAmount, formatDateRange } from '@/features/review/shared/format'
import { STATE_LABELS } from '@/features/review/shared/labels'
import { cn } from '@/lib/utils'

const MICRO_LABEL = 'font-mono text-micro font-semibold tracking-label text-ink-3'

/** A component score is a 0–1 proportion in every rule that emits one bounded value. */
const METER_MAX = 1

function Fact({ label, children }: { readonly label: string; readonly children: React.ReactNode }) {
  return (
    <div>
      <p className={cn('mb-[2px]', MICRO_LABEL)}>{label}</p>
      <p className="text-body-lg font-medium">{children}</p>
    </div>
  )
}

/**
 * Widgets 1–7 — the case header, all of it above the fold.
 *
 * **Reason before score** (display rule 1, `sprint/00-app-spec.md` § 4) is why the primary
 * reason sits in its own block below the identifying facts and above the confidence basis, in
 * DOM order as well as visually. A reader who meets a band or a number first is looking at a
 * different product: the sentence is the finding, and the band is only how urgently to read it.
 */
export function CaseHeader({
  detail,
  onPickAction,
}: {
  readonly detail: CaseDetail
  readonly onPickAction: (action: DispositionAction) => void
}) {
  const [basisOpen, setBasisOpen] = useState(false)
  const primary = detail.primary_reason
  const components = Object.entries(primary?.component_scores ?? {})

  return (
    <section
      aria-label="Kepala kasus"
      className="relative mb-[14px] overflow-hidden rounded-lg border border-line bg-card px-[22px] py-5 shadow-panel"
    >
      <span
        aria-hidden
        className={cn('absolute inset-y-0 left-0 w-[4px]', BAND_RAIL[detail.band.band])}
      />

      {/*
        Fakta di kiri, tindakan di kanan, keduanya rata atas.

        Sebelumnya tombol duduk di `ms-auto` **di dalam** baris fakta. Enam fakta ditambah
        empat tombol tidak pernah muat dalam satu baris pada lebar mana pun yang wajar, jadi
        tombol selalu terdorong ke baris kedua dan meninggalkan dua bidang kosong: di kanan
        badge DATA SINTETIK, dan di kanan deretan tombol itu sendiri — pada layar yang justru
        dipakai demo.

        Kuncinya `flex-1 min-w-0` pada kelompok fakta: ia menyusut dan membungkus **di dalam
        dirinya sendiri** alih-alih mendorong kelompok tombol turun. Tombol tetap di baris
        pertama, rata kanan, dan kedua bidang kosong itu hilang tanpa mengubah urutan baca —
        fakta tetap lebih dulu, kalimat alasan tetap di bawahnya.
      */}
      <div className="mb-4 flex flex-wrap items-start justify-between gap-x-6 gap-y-4 border-b border-line pb-4">
        <div className="flex min-w-0 flex-1 flex-wrap items-center gap-x-[26px] gap-y-4">
        <Fact label="PENGENAL KASUS">
          <span data-numeric className="font-mono text-body-lg">
            {detail.case_id.replace(/^case_/, '').slice(0, 14)}
          </span>
        </Fact>
        <Fact label="NOMINAL KLAIM">
          <span data-numeric>{formatAmount(detail.total_amount)}</span>
        </Fact>
        <Fact label="RENTANG KUNJUNGAN">
          <span data-numeric className="text-body">
            {formatDateRange(detail.encounter_start, detail.encounter_end)}
          </span>
        </Fact>
        <Fact label="PESERTA · FASILITAS">
          <span data-numeric className="font-mono text-body">
            {detail.participant_token} · {detail.provider_token}
          </span>
        </Fact>
        <div>
          <p className={cn('mb-[2px]', MICRO_LABEL)}>STATUS</p>
          <span className="inline-block rounded-md border border-line bg-sunk px-[10px] py-[3px] text-small font-semibold">
            {STATE_LABELS[detail.state]}
          </span>
        </div>
        <span className="rounded-md border border-notice-line bg-notice-bg px-[10px] py-[3px] text-small font-semibold text-notice">
          DATA SINTETIK
        </span>
        </div>

        <div className="flex shrink-0 flex-wrap justify-end gap-2">
          {DISPOSITION_ACTIONS.map((action) => (
            <button
              key={action}
              type="button"
              onClick={() => onPickAction(action)}
              className="rounded-md border border-line bg-card px-[15px] py-[9px] text-small font-semibold transition-colors duration-[var(--motion-fast)] hover:border-brand hover:text-brand"
            >
              {ACTION_LABELS[action]}
            </button>
          ))}
        </div>
      </div>

      {/* Widget 5 — the reason, first. */}
      <p className={cn('mb-[6px]', MICRO_LABEL)}>ALASAN UTAMA</p>
      <h1 className="mb-[14px] max-w-[1000px] text-title font-semibold tracking-title text-pretty">
        {primary
          ? primary.sentence
          : 'Tidak ada risiko teramati pada versi mesin ini. Ini bukan pernyataan bahwa klaimnya bersih.'}
      </h1>

      {/* Widget 6 — the band and its components, below the sentence and collapsed by default. */}
      <div className="flex flex-wrap items-center gap-[10px]">
        <BandBadge band={detail.band.band} />
        <button
          type="button"
          onClick={() => setBasisOpen((open) => !open)}
          aria-expanded={basisOpen}
          aria-controls="dasar-keyakinan"
          className="rounded-md border border-line bg-sunk px-3 py-[6px] text-small font-medium text-brand hover:border-brand"
        >
          Dasar keyakinan {basisOpen ? '▾' : '▸'}
        </button>
      </div>

      {basisOpen ? (
        <div
          id="dasar-keyakinan"
          className="tk-enter mt-[14px] max-w-[1000px] rounded-md border border-line bg-sunk px-[18px] py-4"
        >
          <p className="mb-3 text-small leading-relaxed text-ink-2 text-pretty">
            {detail.band.basis} Pita ini menaikkan prioritas tinjauan — bukan menolak klaim dan
            bukan menyatakan fraud.
          </p>
          {detail.band.caps_applied.length > 0 ? (
            <ul className="mb-3 space-y-1">
              {detail.band.caps_applied.map((cap) => (
                <li key={cap} className="text-small text-ink-2">
                  · {cap}
                </li>
              ))}
            </ul>
          ) : null}
          {components.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {components.map(([name, value]) => (
                <span
                  key={name}
                  className="flex min-w-[140px] flex-col gap-1 rounded-md border border-line bg-card px-3 py-[9px]"
                >
                  <span className="text-meta text-ink-3">{componentLabel(name)}</span>
                  <span data-numeric className="font-mono text-small font-semibold">
                    {value}
                  </span>
                  <span aria-hidden className="h-[4px] overflow-hidden rounded-sm bg-line">
                    <span
                      className="tk-grow-x block h-full bg-brand"
                      style={{
                        width: `${Math.min(METER_MAX, Math.abs(value)) * 100}%`,
                      }}
                    />
                  </span>
                </span>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  )
}

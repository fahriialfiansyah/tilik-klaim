import { ArrowDown, ArrowUp } from 'lucide-react'
import { motion } from 'motion/react'
import { Link, useNavigate } from 'react-router-dom'

import { type SortKey, useQueueStore } from '@/features/review/queue/store'
import { BAND_RAIL, BandBadge } from '@/features/review/shared/components/BandBadge'
import { EvidenceMeter } from '@/features/review/shared/components/EvidenceMeter'
import { formatAge, formatAmount } from '@/features/review/shared/format'
import { MODE_LABELS, STATE_LABELS } from '@/features/review/shared/labels'
import type { CaseSummary } from '@/features/review/shared/types'
import { EASE_OUT, MOTION, seconds } from '@/modules/motion/timing'
import { cn } from '@/lib/utils'

const HEAD_CLASS =
  'border-b border-line px-3 py-[9px] text-left font-mono text-micro font-semibold tracking-label text-ink-3'

/**
 * Baris ke-13 dan seterusnya masuk tanpa jeda tambahan. Setelah itu jeda kumulatifnya
 * lebih panjang daripada waktu yang bersedia ditunggu pembaca, dan sisa daftar sebaiknya
 * sudah ada di sana.
 */
const MAX_STAGGERED_ROWS = 12

/**
 * The band column has one order and the server refuses to invert it, so it must not report a
 * direction that changes. Reporting `descending` there would be a false signal to assistive
 * tech every second click, while the rows sat still.
 */
function ariaSort(
  isActive: boolean,
  sortKey: SortKey,
  order: 'asc' | 'desc',
): 'ascending' | 'descending' | 'other' | 'none' {
  if (!isActive) {
    return 'none'
  }
  if (sortKey === 'band') {
    return 'other'
  }
  return order === 'asc' ? 'ascending' : 'descending'
}

function SortHead({
  label,
  sortKey,
  align = 'left',
  width,
}: {
  readonly label: string
  readonly sortKey: SortKey
  readonly align?: 'left' | 'right'
  readonly width: string
}) {
  const sort = useQueueStore((state) => state.sort)
  const order = useQueueStore((state) => state.order)
  const toggleSort = useQueueStore((state) => state.toggleSort)
  const isActive = sort === sortKey
  const Arrow = order === 'asc' ? ArrowUp : ArrowDown

  return (
    <th
      scope="col"
      style={{ width }}
      className="border-b border-line p-0"
      aria-sort={ariaSort(isActive, sortKey, order)}
    >
      <button
        type="button"
        onClick={() => toggleSort(sortKey)}
        className={cn(
          'flex w-full gap-[5px] px-3 py-[9px] font-mono text-micro font-semibold tracking-label',
          align === 'right' ? 'justify-end' : 'justify-start',
          isActive ? 'text-brand' : 'text-ink-3',
        )}
      >
        {label}
        {/*
          The band column never reverses: the default order is the product's answer to "what do
          I review next", and inverting it would put "tidak ada risiko teramati" at the top of a
          work list. The server refuses it too — this only avoids offering a control that lies.
        */}
        {isActive && sortKey !== 'band' ? <Arrow className="size-3" /> : null}
      </button>
    </th>
  )
}

/**
 * The work list (widget 9).
 *
 * The first column is the **reason sentence in working language**, before any score, band, or
 * amount. `brief/03_ANTREAN_REVIEW.md` § 2.2 and § 10.3 make that a success criterion for the
 * page, not a layout preference: a reader who sees a score first is looking at a different
 * product.
 */
export function QueueTable({ rows }: { readonly rows: readonly CaseSummary[] }) {
  const navigate = useNavigate()

  return (
    <div className="overflow-x-auto">
      <table
        aria-label="Antrean kasus"
        className="w-full min-w-[1240px] table-fixed border-collapse"
      >
        <thead>
          <tr className="bg-sunk">
            <th scope="col" className={cn(HEAD_CLASS, 'pl-4')}>KALIMAT ALASAN</th>
            <th scope="col" style={{ width: '168px' }} className={HEAD_CLASS}>
              MODE RISIKO
            </th>
            <th scope="col" style={{ width: '150px' }} className={HEAD_CLASS}>
              PENGENAL
            </th>
            <SortHead label="BUKTI" sortKey="evidence" width="170px" />
            <SortHead label="NOMINAL" sortKey="amount" align="right" width="140px" />
            <SortHead label="UMUR" sortKey="age" align="right" width="92px" />
            <SortHead label="PITA PRIORITAS" sortKey="band" width="200px" />
            <th scope="col" style={{ width: '150px' }} className={HEAD_CLASS}>
              STATUS
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
              /*
                `layout="position"` menganimasikan perpindahan baris, bukan ukurannya.
                Yang dilayani adalah penyortiran: menekan NOMINAL atau UMUR menyusun ulang
                baris yang sama, dan baris yang meluncur ke tempat barunya memperlihatkan
                bahwa daftar ini memang **terurut** — klaim utama halaman ini — alih-alih
                sekadar berganti isi. Hanya posisi yang dianimasikan, sehingga tidak ada
                koreksi skala yang bisa merusak isi sel.

                Masuknya bertahap dari atas ke bawah, mengikuti urutan yang sama.
              */
              <motion.tr
                key={row.case_id}
                layout="position"
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{
                  duration: seconds(MOTION.base),
                  ease: EASE_OUT,
                  delay: Math.min(index, MAX_STAGGERED_ROWS) * seconds(MOTION.stagger),
                }}
                onClick={() => navigate(`/cases/${row.case_id}`)}
                className="cursor-pointer border-b border-line transition-colors duration-[var(--motion-fast)] hover:bg-sunk"
              >
                <td className="relative p-0">
                  <div className="flex items-start gap-[11px] py-[13px] pr-3 pl-4">
                    <span
                      aria-hidden
                      className={cn(
                        'min-h-[34px] w-[3px] shrink-0 self-stretch rounded-sm',
                        BAND_RAIL[row.band],
                      )}
                    />
                    {/*
                      The reason sentence is the row's one tab stop, and it is a real link so
                      assistive tech announces where it goes. The row's own onClick is a mouse
                      convenience on top of it — putting tabIndex on the <tr> as well would give
                      every row two tab stops and announce neither as navigable.
                    */}
                    <Link
                      to={`/cases/${row.case_id}`}
                      onClick={(event) => event.stopPropagation()}
                      className="min-w-0 rounded-sm text-body-lg font-medium text-pretty text-ink"
                    >
                      {row.reason_sentence}
                    </Link>
                  </div>
                </td>

                <td className="px-3 py-[13px] align-top">
                  {row.modes.length === 0 ? (
                    <span className="text-small text-ink-3">—</span>
                  ) : (
                    <span className="flex flex-wrap gap-1">
                      {row.modes.map((mode) => (
                        <span
                          key={mode}
                          className="inline-block rounded-full border border-band-quiet-line bg-band-quiet-bg px-[9px] py-[2px] text-meta text-band-quiet"
                        >
                          {MODE_LABELS[mode]}
                        </span>
                      ))}
                    </span>
                  )}
                </td>

                <td
                  data-numeric
                  className="px-3 py-[13px] align-top font-mono text-meta text-ink-2"
                >
                  {row.case_id.replace(/^case_/, '').slice(0, 12)}
                </td>

                <td className="px-3 py-[13px] align-top">
                  <EvidenceMeter completeness={row.evidence_completeness} />
                </td>

                <td
                  data-numeric
                  className="px-3 py-[13px] text-right align-top text-body-lg font-medium"
                >
                  {formatAmount(row.total_amount)}
                </td>

                <td data-numeric className="px-3 py-[13px] text-right align-top text-body text-ink-2">
                  {formatAge(row.created_at)}
                </td>

                <td className="px-3 py-[13px] align-top">
                  <BandBadge band={row.band} />
                </td>

                <td className="px-3 py-[13px] align-top text-body text-ink-2">
                  {STATE_LABELS[row.state]}
                </td>
              </motion.tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

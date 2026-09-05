import { Check, Copy, Loader2 } from 'lucide-react'
import { useState, type CSSProperties } from 'react'

import { Button } from '@/components/ui/button'
import { COUNT_ORDER, STATUS_LABELS, countLabel } from '@/features/review/ingest/labels'
import type { BundleRejection } from '@/features/review/ingest/rejection'
import type { IngestBundleResponse, ValidationStatus } from '@/features/review/ingest/types'
import type { ScreenStatus } from '@/features/review/ingest/useIngest'
import { cn } from '@/lib/utils'

/**
 * Three statuses, three visual treatments.
 *
 * `VALID_WITH_NOTES` is amber rather than a paler green: it is a real caveat that changes what
 * a reviewer should do downstream, not a nearly-clean pass. And no status here is green —
 * `design/DESIGN.md` reserves green for a completed, validated *action*, and a bundle passing
 * a shape check is neither.
 */
const STATUS_CLASSES: Record<ValidationStatus, string> = {
  VALID: 'border-line bg-sunk text-ink',
  VALID_WITH_NOTES: 'border-notice-line bg-notice-bg text-notice',
  INVALID: 'border-band-conflict-line bg-band-conflict-bg text-band-conflict',
}

const HASH_PREFIX_LENGTH = 12

/** Widest column count the grid uses; the narrow breakpoint divides it evenly. */
const WIDE_COLUMNS = 3

function fillerCells(shown: number): number {
  return (WIDE_COLUMNS - (shown % WIDE_COLUMNS)) % WIDE_COLUMNS
}

/** Counts in reading order, with anything unrecognised kept rather than dropped. */
function orderedCounts(report: IngestBundleResponse) {
  const known = COUNT_ORDER.map((type) =>
    report.resource_counts.find((count) => count.resource_type === type),
  ).filter((count): count is NonNullable<typeof count> => Boolean(count))
  const rest = report.resource_counts.filter(
    (count) => !COUNT_ORDER.includes(count.resource_type),
  )
  return [...known, ...rest]
}

/**
 * Widgets 4, 5, 8 and 9 — status, resource counts, input hash, and the single screen button.
 *
 * The status is read **before** the error list, because it determines whether the detail needs
 * reading at all (`brief/01_INGEST_VALIDASI.md` § 2.2). And there is exactly one button: no
 * detector picker, no threshold, no mode. That absence is the feature.
 */
export function ValidationReport({
  report,
  rejection,
  screenStatus,
  onScreen,
}: {
  readonly report: IngestBundleResponse | null
  readonly rejection: BundleRejection | null
  readonly screenStatus: ScreenStatus
  readonly onScreen: () => void
}) {
  const [copied, setCopied] = useState(false)
  // A refused bundle is invalid whichever side refused it. The status badge says so rather than
  // leaving the panel on "belum diperiksa" while an error banner sits above it — two places
  // disagreeing about whether anything was checked.
  const status: ValidationStatus | null = rejection ? 'INVALID' : (report?.status ?? null)

  const copyHash = async () => {
    if (!report) {
      return
    }
    try {
      await navigator.clipboard.writeText(report.input_hash)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1600)
    } catch {
      // A denied clipboard permission is not worth an error banner: the hash is on screen and
      // selectable, so the operator can still take it.
      setCopied(false)
    }
  }

  return (
    <section
      aria-label="Laporan validasi"
      className="overflow-hidden rounded-lg border border-line bg-card shadow-panel"
    >
      <div className="flex items-center justify-between gap-3 border-b border-line px-4 py-[14px]">
        <p className="text-small font-semibold">Status validasi</p>
        {status ? (
          <span
            className={cn(
              'rounded-md border px-[11px] py-[3px] text-meta font-semibold',
              STATUS_CLASSES[status],
            )}
          >
            {STATUS_LABELS[status]}
          </span>
        ) : (
          <span className="rounded-md border border-line bg-sunk px-[11px] py-[3px] text-meta text-ink-3">
            Belum diperiksa
          </span>
        )}
      </div>

      {rejection ? (
        <>
          <div className="px-4 py-5">
            <p className="mb-2 text-small leading-relaxed text-pretty">{rejection.message}</p>
            <p
              data-numeric
              className="mb-4 inline-block rounded-sm border border-band-conflict-line bg-band-conflict-bg px-2 py-[2px] font-mono text-meta text-band-conflict"
            >
              {rejection.code}
            </p>
            <p className="text-meta leading-relaxed text-ink-3 text-pretty">
              {rejection.source === 'client'
                ? 'Berkas ditolak di peramban dan tidak dikirim ke layanan. Tidak ada kasus yang dibuat.'
                : 'Layanan menolak berkas ini sebelum menyimpannya. Tidak ada kasus yang dibuat, dan tidak ada penyaringan sebagian.'}
            </p>
          </div>
          {/*
            Disabled rather than absent. Widget 9 says the button is "nonaktif bila tidak sah
            disertai alasan" — a control that vanishes leaves an operator looking for it, and
            keeping it in place is what makes the *reason* the thing they read.
          */}
          <ScreenAction
            isEnabled={false}
            isScreening={false}
            onScreen={onScreen}
            hint="Berkas ini tidak dapat disaring. Perbaiki sesuai kode di atas lalu kirim ulang. Tidak ada penyaringan sebagian."
          />
        </>
      ) : !report ? (
        <div className="px-6 py-[52px] text-center">
          <p className="mb-[6px] text-body-lg font-semibold">Belum ada berkas</p>
          <p className="mx-auto max-w-[420px] text-small text-ink-2 text-pretty">
            Pilih berkas atau salah satu kasus contoh di sebelah kiri. Laporan validasi akan
            terisi di sini.
          </p>
        </div>
      ) : (
        <>
          {/*
            The 1px gaps are the container's own background showing through, which is why the
            last row is padded out: an 11-count grid in three columns leaves one slot empty, and
            an unfilled slot renders as a grey block that reads like a broken cell.
          */}
          <dl className="grid grid-cols-2 gap-px bg-line sm:grid-cols-3">
            {orderedCounts(report).map((count, index) => (
              <div
                key={count.resource_type}
                style={{ '--tk-index': index } as CSSProperties}
                className="tk-enter-fade bg-card px-[15px] py-[13px]"
              >
                <dt className="text-meta text-ink-3">{countLabel(count.resource_type)}</dt>
                <dd
                  data-numeric
                  className={cn(
                    'mt-[2px] text-lead font-semibold',
                    count.count === 0 && 'text-ink-3',
                  )}
                >
                  {count.count}
                </dd>
              </div>
            ))}
            {Array.from({ length: fillerCells(orderedCounts(report).length) }, (_, index) => (
              <div key={`filler-${index}`} aria-hidden className="bg-card" />
            ))}
          </dl>

          <div className="flex items-end justify-between gap-3 border-t border-line px-4 py-[14px]">
            <div className="min-w-0">
              <p className="mb-[3px] font-mono text-micro font-semibold tracking-label text-ink-3">
                SIDIK DIGITAL BERKAS
              </p>
              <p data-numeric className="font-mono text-meta break-all">
                sha256:{report.input_hash.slice(0, HASH_PREFIX_LENGTH)}
                <span className="text-ink-3">
                  {report.input_hash.slice(HASH_PREFIX_LENGTH)}
                </span>
              </p>
            </div>
            <Button variant="outline" size="sm" className="shrink-0" onClick={() => void copyHash()}>
              {copied ? <Check /> : <Copy />}
              {copied ? 'Tersalin' : 'Salin'}
            </Button>
          </div>

          <ScreenAction
            isEnabled={report.is_screenable}
            isScreening={screenStatus === 'screening'}
            onScreen={onScreen}
            hint={
              report.is_screenable
                ? 'Tidak ada langkah konfigurasi. Penyaringan memakai aturan dan versi mesin yang sedang berlaku.'
                : `Berkas berstatus "${STATUS_LABELS[report.status]}", sehingga tidak dapat disaring. Perbaiki sumber daya yang disebut di bawah lalu kirim ulang. Tidak ada penyaringan sebagian.`
            }
          />
        </>
      )}
    </section>
  )
}

/**
 * Widget 9 — the one button, and the sentence under it.
 *
 * Shared by both branches so the control never moves: an operator who has just been told their
 * file is unusable should find the button exactly where it was, disabled, with the reason.
 */
function ScreenAction({
  isEnabled,
  isScreening,
  onScreen,
  hint,
}: {
  readonly isEnabled: boolean
  readonly isScreening: boolean
  readonly onScreen: () => void
  readonly hint: string
}) {
  return (
    <div className="border-t border-line bg-sunk px-4 py-[14px]">
      <Button
        size="lg"
        className="w-full"
        disabled={!isEnabled || isScreening}
        onClick={onScreen}
      >
        {isScreening ? <Loader2 className="animate-spin" /> : null}
        Saring klaim
      </Button>
      <p className="mt-[9px] text-meta leading-relaxed text-ink-3 text-pretty">{hint}</p>
    </div>
  )
}

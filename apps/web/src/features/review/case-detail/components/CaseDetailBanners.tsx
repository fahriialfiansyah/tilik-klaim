import { AlertTriangle, RotateCw } from 'lucide-react'

import { Button } from '@/components/ui/button'
import type { VersionConflict } from '@/features/review/case-detail/useCaseDetail'
import { withStop } from '@/features/review/shared/format'

/**
 * Widget 27 — the stale-version banner.
 *
 * `brief/04_DETAIL_KASUS_DISPOSISI.md` § 4.3 treats overwriting a colleague's decision as an
 * accountability failure rather than a concurrency bug, and it sets three obligations this
 * banner has to meet: say **what changed**, say **who changed it**, and offer a reload — while
 * the reviewer's own input stays untouched on the screen behind it. The panel is deliberately
 * not reset, and the last sentence says so, because the first thing anyone fears on seeing a
 * red banner is that they have to type it all again.
 */
export function VersionConflictBanner({
  conflict,
  onReload,
}: {
  readonly conflict: VersionConflict
  readonly onReload: () => void
}) {
  return (
    <div
      role="alert"
      className="mb-[14px] flex items-start gap-[14px] rounded-lg border border-notice-line bg-notice-bg px-4 py-[14px]"
    >
      <AlertTriangle aria-hidden className="mt-[2px] size-[18px] shrink-0 text-notice" />
      <div className="min-w-0 flex-1">
        <p className="mb-[3px] font-semibold text-notice">
          Versi kasus tidak cocok: kasus ini berubah sejak Anda membukanya
        </p>
        <p className="text-small leading-relaxed text-ink-2 text-pretty">
          {conflict.summary} Perubahan dicatat oleh{' '}
          <strong className="text-ink">{conflict.changedBy}</strong> pada {conflict.changedAt};
          versi kasus berpindah dari {conflict.seenVersion} ke {conflict.currentVersion}.{' '}
          <strong className="text-ink">Isian disposisi Anda tetap dipertahankan</strong>: tidak
          ada yang ditimpa dan tidak ada yang tercatat.
        </p>
      </div>
      <Button variant="outline" size="sm" className="shrink-0" onClick={onReload}>
        <RotateCw />
        Muat ulang
      </Button>
    </div>
  )
}

/** The honest save failure: the service did not answer, and nothing was written. */
export function SaveFailedBanner({
  error,
  onRetry,
}: {
  readonly error: Error | null
  readonly onRetry: () => void
}) {
  return (
    <div
      role="alert"
      className="mb-[14px] flex items-start gap-[14px] rounded-lg border border-band-conflict-line bg-band-conflict-bg px-4 py-[14px]"
    >
      <AlertTriangle aria-hidden className="mt-[2px] size-[18px] shrink-0 text-band-conflict" />
      <div className="min-w-0 flex-1">
        <p className="mb-[3px] font-semibold text-band-conflict">Disposisi gagal disimpan</p>
        <p className="text-small leading-relaxed text-ink-2 text-pretty">
          {withStop(error?.message ?? 'Layanan tidak merespons')} Tidak ada kejadian audit yang tertulis
          sebagian; kejadian ditulis utuh atau tidak sama sekali.{' '}
          <strong className="text-ink">Isian Anda masih utuh di layar.</strong>
        </p>
      </div>
      <Button variant="outline" size="sm" className="shrink-0" onClick={onRetry}>
        <RotateCw />
        Coba lagi
      </Button>
    </div>
  )
}

/**
 * The template caveat, raised out of the drawer to sit above the action buttons.
 *
 * `brief/04_DETAIL_KASUS_DISPOSISI.md` § 2.4 requires it to be readable *before* a reviewer
 * reaches for an action. The drawer carries it too, but a caveat only inside a panel nobody is
 * obliged to open is a caveat that can be skipped past on the way to "konfirmasi anomali".
 */
export function TemplateCaveatBanner({ caveat }: { readonly caveat: string }) {
  return (
    <div
      role="note"
      className="mb-[14px] flex items-start gap-[14px] rounded-lg border border-notice-line bg-notice-bg px-4 py-[14px]"
    >
      <AlertTriangle aria-hidden className="mt-[2px] size-[18px] shrink-0 text-notice" />
      <p className="text-small leading-relaxed text-pretty">
        <span className="font-semibold text-notice">Peringatan templat. </span>
        {caveat}
      </p>
    </div>
  )
}

import { Loader2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'

import { Button } from '@/components/ui/button'
import { ResourceSummary } from '@/features/review/ingest/components/ResourceSummary'
import { TechnicalDetails } from '@/features/review/ingest/components/TechnicalDetails'
import { shortHash } from '@/features/review/ingest/hash'
import { useStatusLabel } from '@/features/review/ingest/labels'
import type { BundleRejection } from '@/features/review/ingest/rejection'
import type { IngestBundleResponse, ValidationStatus } from '@/features/review/ingest/types'
import type { ScreenStatus } from '@/features/review/ingest/useIngest'
import { CopyStateIcon } from '@/modules/clipboard/CopyStateIcon'
import { useCopyState } from '@/modules/clipboard/useCopyState'
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

/**
 * Widgets 4, 5, 8 and 9 — status, resource summary, input hash, and the single screen button.
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
  const { t } = useTranslation('ingest')
  const statusLabel = useStatusLabel()
  const [copyState, copy] = useCopyState()
  // A refused bundle is invalid whichever side refused it. The status badge says so rather than
  // leaving the panel on "not yet checked" while an error banner sits above it — two places
  // disagreeing about whether anything was checked.
  const status: ValidationStatus | null = rejection ? 'INVALID' : (report?.status ?? null)

  return (
    <section
      aria-label={t('report.sectionLabel')}
      className="overflow-hidden rounded-lg border border-line bg-card shadow-panel"
    >
      <div className="flex items-center justify-between gap-3 border-b border-line px-4 py-[14px]">
        <p className="text-small font-semibold">{t('report.heading')}</p>
        {status ? (
          <span
            className={cn(
              'rounded-md border px-[11px] py-[3px] text-meta font-semibold',
              STATUS_CLASSES[status],
            )}
          >
            {statusLabel(status)}
          </span>
        ) : (
          <span className="rounded-md border border-line bg-sunk px-[11px] py-[3px] text-meta text-ink-3">
            {t('report.notChecked')}
          </span>
        )}
      </div>

      {rejection ? (
        <>
          <div className="px-4 py-5">
            <p className="mb-2 text-small leading-relaxed text-pretty">{rejection.message}</p>
            <p className="text-meta leading-relaxed text-ink-3 text-pretty">
              {rejection.source === 'client'
                ? t('report.refusedClient')
                : t('report.refusedServer')}
            </p>
            {/*
              The stable code is what a support request quotes, and nothing a reviewer can act
              on. It stays reachable rather than prominent — see `TechnicalDetails`.
            */}
            <TechnicalDetails code={rejection.code} detail="" />
          </div>
          {/*
            Disabled rather than absent. Widget 9 says the button is disabled-with-a-reason
            when invalid — a control that vanishes leaves an operator looking for it, and
            keeping it in place is what makes the *reason* the thing they read.
          */}
          <ScreenAction
            isEnabled={false}
            isScreening={false}
            onScreen={onScreen}
            hint={t('report.refusedHint')}
          />
        </>
      ) : !report ? (
        <div className="px-6 py-[52px] text-center">
          <p className="mb-[6px] text-body-lg font-semibold">{t('report.emptyTitle')}</p>
          <p className="mx-auto max-w-[420px] text-small text-ink-2 text-pretty">
            {t('report.emptyBody')}
          </p>
        </div>
      ) : (
        <>
          <ResourceSummary counts={report.resource_counts} />

          <div className="flex items-end justify-between gap-3 border-t border-line px-4 py-[14px]">
            <div className="min-w-0">
              <p className="mb-[3px] font-mono text-micro font-semibold tracking-label text-ink-3">
                {t('report.hashHeading')}
              </p>
              <p data-numeric title={report.input_hash} className="font-mono text-meta">
                {shortHash(report.input_hash)}
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              className="shrink-0"
              onClick={() => void copy(report.input_hash)}
            >
              <CopyStateIcon state={copyState} />
              {t(`copy.${copyState}` as 'copy.idle')}
            </Button>
          </div>

          <ScreenAction
            isEnabled={report.is_screenable}
            isScreening={screenStatus === 'screening'}
            onScreen={onScreen}
            hint={
              report.is_screenable
                ? t('report.screenableHint')
                : t('report.notScreenableHint', { status: statusLabel(report.status) })
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
  const { t } = useTranslation('ingest')

  return (
    <div className="border-t border-line bg-sunk px-4 py-[14px]">
      <Button
        size="lg"
        className="w-full"
        disabled={!isEnabled || isScreening}
        onClick={onScreen}
      >
        {isScreening ? <Loader2 className="animate-spin" /> : null}
        {t('report.screen')}
      </Button>
      <p className="mt-[9px] text-meta leading-relaxed text-ink-3 text-pretty">{hint}</p>
    </div>
  )
}

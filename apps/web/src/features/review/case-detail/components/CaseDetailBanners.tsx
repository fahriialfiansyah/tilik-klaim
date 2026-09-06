import { AlertTriangle, RotateCw } from 'lucide-react'
import { Trans, useTranslation } from 'react-i18next'

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
  const { t } = useTranslation('caseDetail')

  return (
    <div
      role="alert"
      className="mb-[14px] flex items-start gap-[14px] rounded-lg border border-notice-line bg-notice-bg px-4 py-[14px]"
    >
      <AlertTriangle aria-hidden className="mt-[2px] size-[18px] shrink-0 text-notice" />
      <div className="min-w-0 flex-1">
        <p className="mb-[3px] font-semibold text-notice">{t('banner.conflictTitle')}</p>
        <p className="text-small leading-relaxed text-ink-2 text-pretty">
          <Trans
            i18nKey="banner.conflictBody"
            ns="caseDetail"
            values={{
              summary: conflict.summary,
              by: conflict.changedBy,
              at: conflict.changedAt,
              seen: conflict.seenVersion,
              current: conflict.currentVersion,
            }}
            components={[
              <span key="0" />,
              <strong key="1" className="text-ink" />,
              <span key="2" />,
              <strong key="3" className="text-ink" />,
            ]}
          />
        </p>
      </div>
      <Button variant="outline" size="sm" className="shrink-0" onClick={onReload}>
        <RotateCw />
        {t('banner.reload')}
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
  const { t } = useTranslation(['caseDetail', 'common'])

  return (
    <div
      role="alert"
      className="mb-[14px] flex items-start gap-[14px] rounded-lg border border-band-conflict-line bg-band-conflict-bg px-4 py-[14px]"
    >
      <AlertTriangle aria-hidden className="mt-[2px] size-[18px] shrink-0 text-band-conflict" />
      <div className="min-w-0 flex-1">
        <p className="mb-[3px] font-semibold text-band-conflict">
          {t('caseDetail:banner.saveFailedTitle')}
        </p>
        <p className="text-small leading-relaxed text-ink-2 text-pretty">
          <Trans
            i18nKey="banner.saveFailedBody"
            ns="caseDetail"
            values={{
              detail: withStop(error?.message ?? t('caseDetail:banner.serviceDown')),
            }}
            components={[<span key="0" />, <strong key="1" className="text-ink" />]}
          />
        </p>
      </div>
      <Button variant="outline" size="sm" className="shrink-0" onClick={onRetry}>
        <RotateCw />
        {t('common:action.retry')}
      </Button>
    </div>
  )
}

/**
 * The template caveat, raised out of the drawer to sit above the action buttons.
 *
 * `brief/04_DETAIL_KASUS_DISPOSISI.md` § 2.4 requires it to be readable *before* a reviewer
 * reaches for an action. The drawer carries it too, but a caveat only inside a panel nobody is
 * obliged to open is a caveat that can be skipped past on the way to confirming an anomaly.
 */
export function TemplateCaveatBanner({ caveat }: { readonly caveat: string }) {
  const { t } = useTranslation('caseDetail')

  return (
    <div
      role="note"
      className="mb-[14px] flex items-start gap-[14px] rounded-lg border border-notice-line bg-notice-bg px-4 py-[14px]"
    >
      <AlertTriangle aria-hidden className="mt-[2px] size-[18px] shrink-0 text-notice" />
      <p className="text-small leading-relaxed text-pretty">
        <span className="font-semibold text-notice">{t('banner.templateCaveat')}</span>
        {caveat}
      </p>
    </div>
  )
}

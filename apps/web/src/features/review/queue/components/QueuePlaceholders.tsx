import { AlertTriangle, Inbox, RotateCw, SlidersHorizontal } from 'lucide-react'
import type { ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { withStop } from '@/features/review/shared/format'

/**
 * The four states that all look like "a table with nothing in it" but mean different things and
 * lead to different next actions.
 *
 * `brief/03_ANTREAN_REVIEW.md` § 4.3 names collapsing them as the most common and most damaging
 * interface defect here: a blank table posing as "no cases" while the service is actually down
 * is a lie the reviewer has no way to detect.
 */

const SKELETON_ROWS = 6

export function QueueLoading() {
  const { t } = useTranslation('queue')

  return (
    <div className="p-4" aria-busy="true" aria-live="polite">
      <span className="sr-only">{t('placeholder.loading')}</span>
      {Array.from({ length: SKELETON_ROWS }, (_, index) => (
        <div key={index} className="flex items-center gap-3 border-b border-line py-[15px]">
          <span className="h-[34px] w-[3px] shrink-0 rounded-sm bg-line" />
          <span className="h-[13px] flex-1 animate-pulse rounded-sm bg-line" />
          <span className="h-[13px] w-[120px] animate-pulse rounded-sm bg-line" />
          <span className="h-[13px] w-[90px] animate-pulse rounded-sm bg-line" />
        </div>
      ))}
    </div>
  )
}

function Placeholder({
  icon,
  title,
  body,
  action,
}: {
  readonly icon: ReactNode
  readonly title: string
  readonly body: string
  readonly action: ReactNode
}) {
  return (
    <div className="px-8 py-[54px] text-center">
      <div className="mb-[18px] flex justify-center text-ink-3">{icon}</div>
      <p className="mb-2 text-lead font-semibold">{title}</p>
      <p className="mx-auto mb-5 max-w-[520px] text-body-lg text-ink-2 text-pretty">{body}</p>
      {action}
    </div>
  )
}

/** Nothing has ever been screened. The next step is Ingest, so say so. */
export function QueueEmpty() {
  const { t } = useTranslation('queue')
  const navigate = useNavigate()

  return (
    <Placeholder
      icon={<Inbox className="size-8" />}
      title={t('placeholder.emptyTitle')}
      body={t('placeholder.emptyBody')}
      action={
        <Button onClick={() => navigate('/ingest')}>{t('placeholder.emptyAction')}</Button>
      }
    />
  )
}

/** Cases exist; this combination of filters just matched none of them. */
export function QueueFilteredEmpty({
  activeFilters,
  onClear,
}: {
  readonly activeFilters: readonly string[]
  readonly onClear: () => void
}) {
  const { t } = useTranslation('queue')

  return (
    <Placeholder
      icon={<SlidersHorizontal className="size-8" />}
      title={t('placeholder.filteredTitle')}
      body={t('placeholder.filteredBody', { filters: activeFilters.join(' + ') })}
      action={<Button onClick={onClear}>{t('placeholder.filteredAction')}</Button>}
    />
  )
}

/** The service did not answer. Never dress this as "no cases". */
export function QueueFailed({
  error,
  onRetry,
}: {
  readonly error: Error | null
  readonly onRetry: () => void
}) {
  const { t } = useTranslation(['queue', 'common'])

  return (
    <Placeholder
      icon={<AlertTriangle className="size-8 text-band-conflict" />}
      title={t('queue:placeholder.failedTitle')}
      body={t('queue:placeholder.failedBody', {
        detail: withStop(error?.message ?? t('queue:placeholder.failedFallback')),
      })}
      action={
        <Button onClick={onRetry}>
          <RotateCw />
          {t('common:action.retry')}
        </Button>
      }
    />
  )
}

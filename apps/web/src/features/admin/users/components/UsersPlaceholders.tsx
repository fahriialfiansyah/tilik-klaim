import { AlertTriangle, RotateCw, Users } from 'lucide-react'
import { Trans, useTranslation } from 'react-i18next'

import { Button } from '@/components/ui/button'

/**
 * The states that all look like an empty table and mean different things.
 *
 * The same rule the queue follows: a blank table posing as "no accounts" while the service is
 * down is a lie the administrator has no way to detect.
 */
const SKELETON_ROWS = 3

/** The script that seeds the roster. Named once, so the copy and the repo cannot disagree. */
const SEED_SCRIPT = 'scripts/seed_dev.py'

export function UsersLoading() {
  const { t } = useTranslation('admin')

  return (
    <div className="p-4" aria-busy="true" aria-live="polite">
      <span className="sr-only">{t('placeholder.loading')}</span>
      {Array.from({ length: SKELETON_ROWS }, (_, index) => (
        <div key={index} className="flex items-center gap-3 border-b border-line py-[15px]">
          <span className="h-[13px] flex-1 animate-pulse rounded-sm bg-line" />
          <span className="h-[13px] w-[110px] animate-pulse rounded-sm bg-line" />
          <span className="h-[13px] w-[80px] animate-pulse rounded-sm bg-line" />
        </div>
      ))}
    </div>
  )
}

export function UsersEmpty() {
  const { t } = useTranslation('admin')

  return (
    <div className="px-8 py-[54px] text-center">
      <div className="mb-[18px] flex justify-center text-ink-3">
        <Users aria-hidden className="size-7" />
      </div>
      <p className="mb-2 text-lead font-semibold">{t('placeholder.emptyTitle')}</p>
      <p className="mx-auto max-w-[520px] text-body-lg text-ink-2 text-pretty">
        <Trans
          i18nKey="placeholder.emptyBody"
          ns="admin"
          values={{ script: SEED_SCRIPT }}
          components={[<span key="0" />, <code key="1" className="font-mono text-body" />]}
        />
      </p>
    </div>
  )
}

export function UsersFailed({ onRetry }: { readonly onRetry: () => void }) {
  const { t } = useTranslation(['admin', 'common'])

  return (
    <div className="px-8 py-[54px] text-center">
      <div className="mb-[18px] flex justify-center text-ink-3">
        <AlertTriangle aria-hidden className="size-7" />
      </div>
      <p className="mb-2 text-lead font-semibold">{t('admin:placeholder.failedTitle')}</p>
      <p className="mx-auto mb-5 max-w-[520px] text-body-lg text-ink-2 text-pretty">
        {t('admin:placeholder.failedBody')}
      </p>
      <Button type="button" variant="outline" onClick={onRetry}>
        <RotateCw aria-hidden className="size-4" />
        {t('common:action.retry')}
      </Button>
    </div>
  )
}

import { useTranslation } from 'react-i18next'

import { PerfectScrollArea } from '@/components/wrappers/PerfectScrollArea'
import { useEventLabel } from '@/features/admin/users/labels'
import type { UserAuditEvent } from '@/features/admin/users/types'
import { roleLabel } from '@/features/auth/labels'
import { isRole } from '@/features/auth/types'
import { formatDateTime } from '@/lib/datetime'
import i18n from '@/modules/i18n/config'

/**
 * The user-management trail, newest first.
 *
 * Append-only, like a case disposition (ADR-0001): there is no control here that edits or
 * removes an entry, and the API has no endpoint that would.
 */
export function UserAuditPanel({
  events,
  nameFor,
}: {
  readonly events: readonly UserAuditEvent[]
  readonly nameFor: (userId: string) => string
}) {
  const { t } = useTranslation('admin')
  const eventLabel = useEventLabel()

  if (events.length === 0) {
    return <p className="px-4 py-6 text-body text-ink-2 text-pretty">{t('audit.empty')}</p>
  }

  return (
    <PerfectScrollArea className="max-h-[360px]">
      <ol className="flex flex-col">
        {events.map((event) => (
          <li key={event.event_id} className="border-b border-line px-4 py-3 last:border-b-0">
            <p className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
              <span className="text-body font-medium text-ink">
                {eventLabel(event.event_kind)}
              </span>
              <span className="text-body text-ink-2">· {nameFor(event.target_user_id)}</span>
              <span data-numeric className="font-mono text-meta text-ink-3">
                {formatDateTime(event.occurred_at)}
              </span>
            </p>
            <p className="mt-[3px] text-meta text-ink-2">
              {readable(event.value_before)} → {readable(event.value_after)}
              <span className="text-ink-3">
                {t('audit.by', {
                  name: nameFor(event.actor_user_id),
                  role: roleLabelOrRaw(event.actor_role),
                })}
              </span>
            </p>
          </li>
        ))}
      </ol>
    </PerfectScrollArea>
  )
}

/** Raw stored values become readable text; anything unrecognised is shown as it was stored. */
function readable(value: string | null): string {
  if (value === null) {
    return '-'
  }
  if (value === 'true') {
    return i18n.t('auth:active.true')
  }
  if (value === 'false') {
    return i18n.t('auth:active.false')
  }
  return isRole(value) ? roleLabel(value) : value
}

function roleLabelOrRaw(role: string): string {
  return isRole(role) ? roleLabel(role) : role
}

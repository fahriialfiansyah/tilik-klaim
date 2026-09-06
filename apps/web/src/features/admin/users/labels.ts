import { useTranslation } from 'react-i18next'

import type { UserAuditEvent } from '@/features/admin/users/types'

/**
 * Column headings, in the order the table renders them.
 *
 * **`ID Petugas`, not `Token`.** In this codebase "token" means authentication material —
 * `X-Internal-Token`, a Bearer JWT — and `PTG-01` is an employee code that grants nothing and is
 * safe on screen. The column was named after the thing it is least like.
 *
 * **There is no actions column.** It held one sentence on one row of three, leaving two cells
 * permanently blank and announcing an empty column to a screen reader. What lived there was
 * never column data: "you cannot edit your own account" is a fact about a row, so it sits under
 * that row's name, and "saving" is the state of a control, so it sits on the control.
 *
 * The order is fixed here rather than in the locale file: a translator reordering a JSON object
 * would reorder the table, and the headings must stay aligned with the cells beneath them.
 */
export const COLUMN_KEYS = [
  'name',
  'staffCode',
  'email',
  'role',
  'status',
  'lastSignIn',
] as const

export function useColumns(): readonly string[] {
  const { t } = useTranslation('admin')
  return COLUMN_KEYS.map((key) => t(`column.${key}` as 'column.name'))
}

export function useEventLabel(): (kind: UserAuditEvent['event_kind']) => string {
  const { t } = useTranslation('admin')
  return (kind) => t(`event.${kind}` as 'event.USER_ROLE_CHANGED')
}

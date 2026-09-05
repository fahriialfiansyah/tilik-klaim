import type { UserAuditEvent } from '@/features/admin/users/types'

/**
 * Column headings, in the order the table renders them.
 *
 * **`ID Petugas`, not `Token`.** In this codebase "token" means authentication material —
 * `X-Internal-Token`, a Bearer JWT — and `PTG-01` is an employee code that grants nothing and is
 * safe on screen. The column named it after the thing it is least like.
 *
 * **There is no `Tindakan` column.** It held one sentence on one row of three, leaving two cells
 * permanently blank and announcing an empty column to a screen reader. What lived there was
 * never column data: "you cannot edit your own account" is a fact about a row, so it sits under
 * that row's name, and "saving" is the state of a control, so it sits on the control.
 */
export const COLUMNS = [
  'Nama',
  'ID Petugas',
  'Email',
  'Peran',
  'Status',
  'Terakhir masuk',
] as const

export const EVENT_LABEL: Readonly<Record<UserAuditEvent['event_kind'], string>> = {
  USER_ROLE_CHANGED: 'Peran diubah',
  USER_DEACTIVATED: 'Akun dinonaktifkan',
  USER_REACTIVATED: 'Akun diaktifkan kembali',
}

export const NEVER_SIGNED_IN = 'Belum pernah'

/** Said beside the signed-in administrator's own name, where the `ANDA` badge already is. */
export const SELF_ROW_NOTE = 'Akun sendiri tidak dapat diubah'

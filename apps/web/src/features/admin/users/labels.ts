import type { UserAuditEvent } from '@/features/admin/users/types'

/** Column headings, in the order the table renders them. */
export const COLUMNS = [
  'Nama',
  'Token',
  'Email',
  'Peran',
  'Status',
  'Terakhir masuk',
  'Tindakan',
] as const

export const EVENT_LABEL: Readonly<Record<UserAuditEvent['event_kind'], string>> = {
  USER_ROLE_CHANGED: 'Peran diubah',
  USER_DEACTIVATED: 'Akun dinonaktifkan',
  USER_REACTIVATED: 'Akun diaktifkan kembali',
}

export const NEVER_SIGNED_IN = 'Belum pernah'

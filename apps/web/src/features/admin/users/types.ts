import type { StaffUser } from '@/features/auth/types'

/** One recorded change to one account. Append-only — nothing edits or removes these. */
export type UserAuditEvent = {
  readonly event_id: string
  readonly event_kind: 'USER_ROLE_CHANGED' | 'USER_DEACTIVATED' | 'USER_REACTIVATED'
  readonly actor_user_id: string
  readonly actor_role: string
  readonly target_user_id: string
  readonly field: string
  readonly value_before: string | null
  readonly value_after: string | null
  readonly occurred_at: string
}

export type UserListResponse = { readonly users: readonly StaffUser[] }
export type UserAuditResponse = { readonly events: readonly UserAuditEvent[] }
export type UserUpdateResponse = {
  readonly user: StaffUser
  readonly events: readonly UserAuditEvent[]
}

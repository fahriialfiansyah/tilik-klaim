/**
 * The three roles, and the account shape the API returns.
 *
 * Identifiers are English; the labels in `labels.ts` are Indonesian, as everywhere else.
 * `docs/canonical/decisions/ADR-0006-three-roles-and-simulated-login.md` § 1 is the authority —
 * `auditor` was retired there, and there is no fourth role.
 */
export const ROLES = ['reviewer', 'senior_reviewer', 'admin'] as const

export type Role = (typeof ROLES)[number]

/** One synthetic staff account. Never carries a passcode — the API does not return one. */
export type StaffUser = {
  readonly user_id: string
  readonly staff_token: string
  readonly full_name: string
  readonly email: string
  readonly role: Role
  readonly is_active: boolean
  readonly last_signed_in_at: string | null
}

export type SessionResponse = {
  readonly user: StaffUser
}

export function isRole(value: string): value is Role {
  return (ROLES as readonly string[]).includes(value)
}

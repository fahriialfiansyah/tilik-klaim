import accessMatrix from '@/features/auth/access-matrix.json'
import type { Role } from '@/features/auth/types'

/**
 * The access matrix as the login screen shows it.
 *
 * `access-matrix.json` is **generated** from `app/service/access.py` by
 * `apps/backend/scripts/export_access_matrix.py`, and a backend test fails when the committed
 * file drifts from the server. That matters more here than anywhere else in the app: this page
 * *is* the matrix, so a hand-maintained copy would be a screen that quietly lies about what the
 * server permits.
 */
export type CapabilityKey = (typeof accessMatrix.capabilities)[number]

/** Roles in the order the table lists them: least authority first. */
export const MATRIX_ROLES: readonly Role[] = ['reviewer', 'senior_reviewer', 'admin']

/**
 * A working-language name for every capability the server knows.
 *
 * All nine, not the six the login table shows: the admin page renders what a role change
 * *grants and takes away*, and a capability with no label would appear there as a blank line —
 * a change described by saying nothing about it. `matrix.test.ts` asserts this map covers
 * `ALL_CAPABILITIES`, so a capability added to `app/service/access.py` fails a test here rather
 * than rendering empty in front of an administrator.
 */
export const CAPABILITY_LABEL: Readonly<Record<string, string>> = {
  READ_CASES: 'Antrean & Detail Kasus',
  RECORD_DISPOSITION: 'Catat disposisi',
  REOPEN_DISMISSED_CASE: 'Buka kembali kasus ditolak',
  READ_CASE_AUDIT: 'Baca riwayat audit kasus',
  INGEST_BUNDLE: 'Ingest / Demo',
  READ_EVALUATION: 'Audit & Evaluasi',
  REQUEST_BRIEFING: 'Minta Ringkasan bukti',
  MANAGE_USERS: 'Manajemen pengguna',
  READ_USER_AUDIT: 'Baca audit manajemen pengguna',
}

/**
 * The six columns the login screen shows, and the words above them.
 *
 * Six of the nine capabilities, chosen because each one names a page or an act a reviewer would
 * recognise. The three left out — reading a case's audit trail, reading the user-management
 * trail, and asking for an evidence summary — follow their surrounding capability exactly and
 * would add three columns that never disagree with a neighbour. The screen says so in a footnote
 * and points at ADR-0006 § 2 for the full table; `matrix.test.ts` asserts every column here
 * exists in the generated file, so a column can never be invented.
 *
 * Labels come from `CAPABILITY_LABEL` rather than being repeated here — two lists of names for
 * one set of capabilities is two lists that drift.
 */
export const MATRIX_COLUMN_KEYS = [
  'READ_CASES',
  'RECORD_DISPOSITION',
  'REOPEN_DISMISSED_CASE',
  'INGEST_BUNDLE',
  'READ_EVALUATION',
  'MANAGE_USERS',
] as const

export const MATRIX_COLUMNS: readonly { key: CapabilityKey; label: string }[] =
  MATRIX_COLUMN_KEYS.map((key) => ({
    key: key as CapabilityKey,
    label: CAPABILITY_LABEL[key] ?? key,
  }))

/** Every capability the server grants this role. Read from the generated file, never guessed. */
export function capabilitiesFor(role: Role): readonly string[] {
  return accessMatrix.roles[role] ?? []
}

/** May this role do this? The same question the server answers, asked of the same table. */
export function allows(role: Role, capability: CapabilityKey): boolean {
  return capabilitiesFor(role).includes(capability)
}

/** Every capability name the server knows about. */
export const ALL_CAPABILITIES: readonly string[] = accessMatrix.capabilities

/** What a move from one role to another actually gives and takes away. */
export type CapabilityChange = {
  readonly granted: readonly string[]
  readonly revoked: readonly string[]
}

/**
 * The consequence of a role change, read off the generated matrix.
 *
 * An administrator picking "Peninjau Senior" from a dropdown is granting the authority to
 * reopen a case someone else dismissed. The dropdown does not say that, and the role name only
 * says it to somebody who already knows ADR-0006 § 2 — so the confirmation dialog spells it out
 * before the change is sent, in the same words the login screen uses for the same capability.
 *
 * Computed from `access-matrix.json`, which is generated from the server's own `CAPABILITIES`.
 * A hand-written "changing to senior grants reopening" would be a sentence that keeps its
 * confidence long after the server stops agreeing with it.
 */
export function capabilityChange(from: Role, to: Role): CapabilityChange {
  const before = new Set(capabilitiesFor(from))
  const after = new Set(capabilitiesFor(to))
  return {
    granted: [...after].filter((capability) => !before.has(capability)).sort(),
    revoked: [...before].filter((capability) => !after.has(capability)).sort(),
  }
}

/** The capability's working-language name, or its raw key if the server grew one we have not named. */
export function capabilityLabel(capability: string): string {
  return CAPABILITY_LABEL[capability] ?? capability
}

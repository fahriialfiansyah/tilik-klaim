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
 * The six columns the screen shows, and the words above them.
 *
 * Six of the nine capabilities, chosen because each one names a page or an act a reviewer would
 * recognise. The three left out — reading a case's audit trail, reading the user-management
 * trail, and asking for an evidence summary — follow their surrounding capability exactly and
 * would add three columns that never disagree with a neighbour. The screen says so in a footnote
 * and points at ADR-0006 § 2 for the full table; `matrix.test.ts` asserts every column here
 * exists in the generated file, so a column can never be invented.
 */
export const MATRIX_COLUMNS: readonly { key: CapabilityKey; label: string }[] = [
  { key: 'READ_CASES', label: 'Antrean & Detail Kasus' },
  { key: 'RECORD_DISPOSITION', label: 'Catat disposisi' },
  { key: 'REOPEN_DISMISSED_CASE', label: 'Buka kembali kasus ditolak' },
  { key: 'INGEST_BUNDLE', label: 'Ingest / Demo' },
  { key: 'READ_EVALUATION', label: 'Audit & Evaluasi' },
  { key: 'MANAGE_USERS', label: 'Manajemen pengguna' },
] as const

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

import accessMatrix from '@/features/auth/access-matrix.json'
import type { Role } from '@/features/auth/types'
import { translateOr } from '@/modules/i18n/translateOr'

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
 * Every capability the server knows, by name, in the reader's language.
 *
 * All ten, not the six the login table shows: the admin page renders what a role change
 * *grants and takes away*, and a capability with no name would appear there as a blank line —
 * a change described by saying nothing about it. `matrix.test.ts` asserts every capability in
 * `ALL_CAPABILITIES` resolves in both languages, so a capability added to
 * `app/service/access.py` fails a test here rather than rendering empty in front of an
 * administrator.
 *
 * The names live in `auth:capability.*` rather than in a constant here, because a constant is
 * read once at module load and would keep its language after the header switch.
 */
export const CAPABILITY_KEYS: readonly string[] = [
  'READ_CASES',
  'RECORD_DISPOSITION',
  'REOPEN_DISMISSED_CASE',
  'READ_CASE_AUDIT',
  'INGEST_BUNDLE',
  'READ_EVALUATION',
  'REQUEST_BRIEFING',
  'ASK_ASSISTANT',
  'MANAGE_USERS',
  'READ_USER_AUDIT',
] as const

/**
 * The six columns the login screen shows.
 *
 * Six of the ten capabilities, chosen because each one names a page or an act a reviewer would
 * recognise. The four left out — reading a case's audit trail, reading the user-management
 * trail, asking for an evidence summary, and asking the Evidence Assistant — follow their
 * surrounding capability exactly and would add four columns that never disagree with a
 * neighbour. The screen says so in a footnote
 * and points at ADR-0006 § 2 for the full table; `matrix.test.ts` asserts every column here
 * exists in the generated file, so a column can never be invented.
 *
 * Names come from `capabilityLabel` rather than being repeated here — two lists of names for
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

/**
 * The columns, resolved at render time.
 *
 * A function rather than a constant array for the same reason the labels moved: a module-level
 * array would freeze its headings in whichever language happened to be active when the bundle
 * first evaluated.
 */
export function matrixColumns(): readonly { key: CapabilityKey; label: string }[] {
  return MATRIX_COLUMN_KEYS.map((key) => ({
    key: key as CapabilityKey,
    label: capabilityLabel(key),
  }))
}

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

/** The capability's name, or its raw key if the server grew one we have not named. */
export function capabilityLabel(capability: string): string {
  return translateOr(`auth:capability.${capability}`, capability)
}

import { describe, expect, test } from 'vitest'

import {
  ALL_CAPABILITIES,
  CAPABILITY_LABEL,
  MATRIX_COLUMNS,
  MATRIX_ROLES,
  allows,
  capabilityChange,
  capabilityLabel,
} from '@/features/auth/matrix'
import { ROLES } from '@/features/auth/types'

describe('the matrix the login screen renders', () => {
  test('lists every role the server knows, and no others', () => {
    expect([...MATRIX_ROLES].sort()).toEqual([...ROLES].sort())
  })

  test('every displayed column is a real capability, never an invented one', () => {
    // The page *is* the matrix. A column that exists only in the UI would be the screen
    // claiming the server enforces something it has never heard of.
    for (const column of MATRIX_COLUMNS) {
      expect(ALL_CAPABILITIES, column.key).toContain(column.key)
    }
  })

  test('reproduces the ADR-0006 § 2 rows the page is judged on', () => {
    expect(allows('reviewer', 'READ_CASES')).toBe(true)
    expect(allows('reviewer', 'REOPEN_DISMISSED_CASE')).toBe(false)
    expect(allows('senior_reviewer', 'REOPEN_DISMISSED_CASE')).toBe(true)
    expect(allows('reviewer', 'MANAGE_USERS')).toBe(false)
    expect(allows('admin', 'MANAGE_USERS')).toBe(true)
  })

  test('an administrator is refused every reviewing column', () => {
    // Separation of duties, asserted as a property rather than six separate lines.
    const reviewing = MATRIX_COLUMNS.filter((column) => column.key !== 'MANAGE_USERS')
    for (const column of reviewing) {
      expect(allows('admin', column.key), column.key).toBe(false)
    }
  })
})

describe('what a role change actually moves', () => {
  test('names the one capability that separates a reviewer from a senior one', () => {
    // The dropdown says "Peninjau Senior". This is what choosing it hands over.
    const { granted, revoked } = capabilityChange('reviewer', 'senior_reviewer')
    expect(granted).toEqual(['REOPEN_DISMISSED_CASE'])
    expect(revoked).toEqual([])
  })

  test('a promotion to admin is a removal, and says so', () => {
    // The move most likely to be made carelessly: `admin` reads as "more", and it takes the
    // entire queue away. A dialog that only listed grants would describe this as a gain.
    const { granted, revoked } = capabilityChange('reviewer', 'admin')
    expect(granted).toEqual(['MANAGE_USERS', 'READ_USER_AUDIT'])
    expect(revoked).toContain('READ_CASES')
    expect(revoked).toContain('RECORD_DISPOSITION')
  })

  test('is symmetric — undoing a change moves exactly what the change moved', () => {
    const forward = capabilityChange('reviewer', 'admin')
    const back = capabilityChange('admin', 'reviewer')
    expect(back.granted).toEqual(forward.revoked)
    expect(back.revoked).toEqual(forward.granted)
  })

  test('a role changed to itself moves nothing', () => {
    expect(capabilityChange('admin', 'admin')).toEqual({ granted: [], revoked: [] })
  })

  test('every capability the server knows has a name a person can read', () => {
    // A capability the server grows but this app has not named would render as a blank line in
    // the confirmation dialog — a change described by saying nothing about it.
    for (const capability of ALL_CAPABILITIES) {
      expect(CAPABILITY_LABEL, capability).toHaveProperty(capability)
      expect(capabilityLabel(capability), capability).not.toBe('')
    }
  })

  test('an unknown capability falls back to its key rather than vanishing', () => {
    expect(capabilityLabel('SOMETHING_NEW')).toBe('SOMETHING_NEW')
  })
})

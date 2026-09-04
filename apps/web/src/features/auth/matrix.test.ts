import { describe, expect, test } from 'vitest'

import { ALL_CAPABILITIES, MATRIX_COLUMNS, MATRIX_ROLES, allows } from '@/features/auth/matrix'
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

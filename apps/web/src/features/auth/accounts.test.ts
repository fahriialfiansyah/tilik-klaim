import { describe, expect, test } from 'vitest'

import { DEMO_ACCOUNTS, credentialLine } from '@/features/auth/accounts'
import { ROLES } from '@/features/auth/types'

describe('demo accounts', () => {
  test('there are exactly three, one per role', () => {
    expect(DEMO_ACCOUNTS).toHaveLength(3)
    expect(DEMO_ACCOUNTS.map((account) => account.role).sort()).toEqual([...ROLES].sort())
  })

  test('every email uses the reserved .example TLD so none can resolve', () => {
    for (const account of DEMO_ACCOUNTS) {
      expect(account.email, account.staffToken).toMatch(/\.example$/)
    }
  })

  test('the copied line carries both halves needed to sign in', () => {
    const line = credentialLine(DEMO_ACCOUNTS[0])
    expect(line).toContain(DEMO_ACCOUNTS[0].email)
    expect(line).toContain(DEMO_ACCOUNTS[0].passcode)
  })
})

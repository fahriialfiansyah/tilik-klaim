import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, test, vi } from 'vitest'

import { UserTable } from '@/features/admin/users/components/UserTable'
import type { StaffUser } from '@/features/auth/types'
import { renderWithRouter } from '@/test/render'

const ROSTER: readonly StaffUser[] = [
  {
    user_id: 'usr_sari_wulandari',
    staff_token: 'PTG-01',
    full_name: 'Sari Wulandari',
    email: 'sari.wulandari@rsud-demo.example',
    role: 'reviewer',
    is_active: true,
    last_signed_in_at: '2026-09-04T02:15:00Z',
  },
  {
    user_id: 'usr_rina_hartati',
    staff_token: 'PTG-03',
    full_name: 'Rina Hartati',
    email: 'rina.hartati@rsud-demo.example',
    role: 'admin',
    is_active: true,
    last_signed_in_at: null,
  },
]

function renderTable(overrides: Partial<Parameters<typeof UserTable>[0]> = {}) {
  const onChangeRole = vi.fn()
  const onToggleActive = vi.fn()
  renderWithRouter(
    <UserTable
      users={ROSTER}
      selfId="usr_rina_hartati"
      pendingUserId={null}
      onChangeRole={onChangeRole}
      onToggleActive={onToggleActive}
      {...overrides}
    />,
  )
  return { onChangeRole, onToggleActive }
}

function rowFor(name: string) {
  return screen.getByRole('rowheader', { name: new RegExp(name) }).closest('tr') as HTMLElement
}

describe('user table', () => {
  test('is a real table with column headers and a row header per account', () => {
    renderTable()
    expect(screen.getAllByRole('columnheader')).toHaveLength(7)
    expect(screen.getAllByRole('rowheader')).toHaveLength(2)
  })

  test('changing a role reports the new role for that account', async () => {
    const { onChangeRole } = renderTable()
    await userEvent.selectOptions(
      within(rowFor('Sari Wulandari')).getByRole('combobox'),
      'senior_reviewer',
    )
    expect(onChangeRole).toHaveBeenCalledWith('usr_sari_wulandari', 'senior_reviewer')
  })

  test('deactivating reports the flag rather than a toggle with no value', async () => {
    const { onToggleActive } = renderTable()
    await userEvent.click(within(rowFor('Sari Wulandari')).getByRole('checkbox'))
    expect(onToggleActive).toHaveBeenCalledWith('usr_sari_wulandari', false)
  })

  test('the signed-in administrator cannot change their own row, and is told why', () => {
    renderTable()
    const own = rowFor('Rina Hartati')

    expect(within(own).getByRole('combobox')).toBeDisabled()
    expect(within(own).getByRole('checkbox')).toBeDisabled()
    expect(within(own).getByText('Akun sendiri tidak dapat diubah')).toBeInTheDocument()
  })

  test('status carries a word, never colour alone', () => {
    renderTable()
    expect(within(rowFor('Sari Wulandari')).getByText('Aktif')).toBeInTheDocument()
  })

  test('an account that never signed in says so rather than showing a dash', () => {
    renderTable()
    // A dash reads as missing data. "Belum pernah" is a fact about the account.
    expect(within(rowFor('Rina Hartati')).getByText('Belum pernah')).toBeInTheDocument()
  })

  test('a row being saved disables its controls', () => {
    renderTable({ pendingUserId: 'usr_sari_wulandari' })
    const row = rowFor('Sari Wulandari')
    expect(within(row).getByRole('combobox')).toBeDisabled()
    expect(within(row).getByText('Menyimpan…')).toBeInTheDocument()
  })
})

import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, test, vi } from 'vitest'

import { UserTable } from '@/features/admin/users/components/UserTable'
import type { StaffUser } from '@/features/auth/types'
import { renderWithRouter } from '@/test/render'

const ROSTER: readonly StaffUser[] = [
  {
    user_id: 'usr_sari_wulandari',
    staff_code: 'PTG-01',
    full_name: 'Sari Wulandari',
    email: 'sari.wulandari@rsud-demo.example',
    role: 'reviewer',
    is_active: true,
    last_signed_in_at: '2026-09-04T02:15:00Z',
  },
  {
    user_id: 'usr_rina_hartati',
    staff_code: 'PTG-03',
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
    // Six, not seven: the `Tindakan` column held one sentence on one row and announced an
    // empty column on the other two.
    expect(screen.getAllByRole('columnheader')).toHaveLength(6)
    expect(screen.getAllByRole('rowheader')).toHaveLength(2)
  })

  test('no column is announced with nothing in it', () => {
    renderTable()
    // The reason the actions column was removed: a screen reader read out "Tindakan" and then
    // silence for two of the three rows.
    expect(screen.queryByRole('columnheader', { name: 'Tindakan' })).not.toBeInTheDocument()
  })

  test('the ID column is named for what it holds, not for a token', () => {
    renderTable()
    expect(screen.getByRole('columnheader', { name: 'ID Petugas' })).toBeInTheDocument()
    expect(screen.queryByRole('columnheader', { name: 'Token' })).not.toBeInTheDocument()
  })

  test('a sign-in time names its time zone rather than leaving it to the reader', () => {
    renderTable()
    // 02:15 UTC is 09.15 in Jakarta. Both halves matter: the hour proves the zone is pinned
    // rather than the viewer's, and the label proves the reader is told which zone that is.
    expect(within(rowFor('Sari Wulandari')).getByText(/09\.15 WIB/)).toBeInTheDocument()
  })

  test('changing a role reports the new role for that account', async () => {
    const { onChangeRole } = renderTable()
    await userEvent.selectOptions(
      within(rowFor('Sari Wulandari')).getByRole('combobox'),
      'senior_reviewer',
    )
    expect(onChangeRole).toHaveBeenCalledWith(ROSTER[0], 'senior_reviewer')
  })

  test('deactivating reports the flag rather than a toggle with no value', async () => {
    const { onToggleActive } = renderTable()
    await userEvent.click(within(rowFor('Sari Wulandari')).getByRole('checkbox'))
    expect(onToggleActive).toHaveBeenCalledWith(ROSTER[0], false)
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

  test('a row being saved disables its controls and says so on the row', () => {
    renderTable({ pendingUserId: 'usr_sari_wulandari' })
    const row = rowFor('Sari Wulandari')
    expect(within(row).getByRole('combobox')).toBeDisabled()
    expect(within(row).getByRole('status')).toHaveTextContent('Menyimpan…')
    expect(row).toHaveAttribute('aria-busy', 'true')
  })
})

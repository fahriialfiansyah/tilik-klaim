import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, test, vi } from 'vitest'

import {
  ConfirmUserChange,
  type PendingChange,
} from '@/features/admin/users/components/ConfirmUserChange'
import type { StaffUser } from '@/features/auth/types'
import { renderWithRouter } from '@/test/render'

const SARI: StaffUser = {
  user_id: 'usr_sari_wulandari',
  staff_code: 'PTG-01',
  full_name: 'Sari Wulandari',
  email: 'sari.wulandari@rsud-demo.example',
  role: 'reviewer',
  is_active: true,
  last_signed_in_at: '2026-09-04T02:15:00Z',
}

function renderDialog(change: PendingChange | null) {
  const onCancel = vi.fn()
  const onConfirm = vi.fn()
  renderWithRouter(
    <ConfirmUserChange change={change} onCancel={onCancel} onConfirm={onConfirm} />,
  )
  return { onCancel, onConfirm }
}

describe('confirming a role change', () => {
  const PROMOTION: PendingChange = { kind: 'role', user: SARI, role: 'senior_reviewer' }

  test('names the capability the change hands over, not just the new role name', () => {
    renderDialog(PROMOTION)
    expect(screen.getByRole('dialog')).toHaveTextContent('Ubah peran Sari Wulandari?')
    expect(screen.getByText('Buka kembali kasus ditolak')).toBeInTheDocument()
  })

  test('shows what a move to admin takes away, not only what it grants', () => {
    // The dialog exists for this case: `admin` reads as "more" and removes the entire queue.
    renderDialog({ kind: 'role', user: SARI, role: 'admin' })
    const dialog = screen.getByRole('dialog')
    expect(dialog).toHaveTextContent('Manajemen pengguna')
    expect(dialog).toHaveTextContent('Antrean & Detail Kasus')
    expect(dialog).toHaveTextContent('Catat disposisi')
  })

  test('says so plainly when a direction grants nothing', () => {
    renderDialog({ kind: 'role', user: { ...SARI, role: 'senior_reviewer' }, role: 'reviewer' })
    expect(screen.getByText('Tidak ada kemampuan baru.')).toBeInTheDocument()
  })

  test('reports the change only when it is confirmed', async () => {
    const { onConfirm } = renderDialog(PROMOTION)
    await userEvent.click(screen.getByRole('button', { name: 'Ubah peran' }))
    expect(onConfirm).toHaveBeenCalledWith(PROMOTION)
  })

  test('cancelling reports a cancel and never a change', async () => {
    const { onCancel, onConfirm } = renderDialog(PROMOTION)
    await userEvent.click(screen.getByRole('button', { name: 'Batal' }))
    expect(onCancel).toHaveBeenCalled()
    expect(onConfirm).not.toHaveBeenCalled()
  })
})

describe('confirming a deactivation', () => {
  test('says what happens to the work already recorded', () => {
    // An administrator cannot check this from here — this page reaches no case, by design.
    // Leaving them to guess is how a reversible act gets treated as an irreversible one.
    renderDialog({ kind: 'deactivate', user: SARI })
    const dialog = screen.getByRole('dialog')
    expect(dialog).toHaveTextContent('Nonaktifkan akun Sari Wulandari?')
    expect(dialog).toHaveTextContent(/Disposisi yang sudah dicatat tetap tercatat/)
    expect(dialog).toHaveTextContent(/dapat mengaktifkannya kembali/)
  })
})

describe('when nothing is pending', () => {
  test('no dialog is shown', () => {
    renderDialog(null)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})

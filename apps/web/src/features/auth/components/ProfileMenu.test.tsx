import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, test } from 'vitest'

import { ProfileMenu } from '@/features/auth/components/ProfileMenu'
import { useSession } from '@/features/auth/useSession'
import { EMPTY_DRAFT, useCaseDetailStore } from '@/features/review/case-detail/store'
import type { StaffUser } from '@/features/auth/types'
import { renderWithRouter } from '@/test/render'

const SARI: StaffUser = {
  user_id: 'usr_sari_wulandari',
  staff_token: 'PTG-01',
  full_name: 'Sari Wulandari',
  email: 'sari.wulandari@rsud-demo.example',
  role: 'reviewer',
  is_active: true,
  last_signed_in_at: null,
}

beforeEach(() => {
  useSession.setState({ user: SARI })
  useCaseDetailStore.setState({ drafts: {} })
})

/** Opens the menu and hands back the trigger, captured before Radix rewrites its attributes. */
async function openMenu() {
  renderWithRouter(<ProfileMenu />)
  const trigger = screen.getByRole('button', { name: /Sari Wulandari/ })
  await userEvent.click(trigger)
  await screen.findByRole('menu')
  return trigger
}

describe('profile menu', () => {
  test('shows the person, their email, role and staff token', async () => {
    await openMenu()
    expect(screen.getAllByText('Sari Wulandari').length).toBeGreaterThan(0)
    expect(screen.getByText(SARI.email)).toBeInTheDocument()
    expect(screen.getAllByText('Peninjau').length).toBeGreaterThan(0)
    expect(screen.getAllByText('PTG-01').length).toBeGreaterThan(0)
  })

  test('Escape closes it and returns focus to the trigger', async () => {
    const trigger = await openMenu()

    await userEvent.keyboard('{Escape}')

    await waitFor(() => expect(screen.queryByRole('menu')).not.toBeInTheDocument())
    // Radix returns focus to its own trigger, which a dropdown always has — unlike the
    // drawers, which are opened from ordinary buttons and restore focus by hand.
    expect(trigger).toHaveFocus()
  })

  test('signing out with no draft clears the session immediately', async () => {
    await openMenu()
    await userEvent.click(screen.getByRole('menuitem', { name: /Keluar/ }))
    expect(useSession.getState().user).toBeNull()
  })

  test('signing out with an unsaved draft warns before discarding it', async () => {
    useCaseDetailStore.setState({
      drafts: { case_1: { ...EMPTY_DRAFT, structuredReason: 'Bukti belum dilampirkan.' } },
    })
    await openMenu()

    await userEvent.click(screen.getByRole('menuitem', { name: /Keluar/ }))

    // Still signed in: the first press asks rather than acts. `store.ts` keeps drafts alive so
    // a refused save costs nothing, and a silent sign-out would undo that from another angle.
    expect(useSession.getState().user).not.toBeNull()
    expect(screen.getByText(/belum tersimpan/)).toBeInTheDocument()

    await userEvent.click(screen.getByRole('menuitem', { name: /Keluar dan buang draf/ }))
    expect(useSession.getState().user).toBeNull()
  })

  test('a half-filled note counts as unsaved work', async () => {
    useCaseDetailStore.setState({
      drafts: { case_1: { ...EMPTY_DRAFT, note: 'Menunggu konfirmasi bagian rekam medis.' } },
    })
    await openMenu()
    await userEvent.click(screen.getByRole('menuitem', { name: /Keluar/ }))
    expect(useSession.getState().user).not.toBeNull()
  })

  test('a draft that only pre-ticked itself is not treated as the reviewer\'s work', async () => {
    // `evidenceSeeded` is the system's doing, not the reviewer's — warning about it would cry
    // wolf on a case nobody has touched.
    useCaseDetailStore.setState({
      drafts: { case_1: { ...EMPTY_DRAFT, evidenceSeeded: true } },
    })
    await openMenu()
    await userEvent.click(screen.getByRole('menuitem', { name: /Keluar/ }))
    expect(useSession.getState().user).toBeNull()
  })
})

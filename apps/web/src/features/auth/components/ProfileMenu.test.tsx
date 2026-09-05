import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, test } from 'vitest'

import { ProfileMenu } from '@/features/auth/components/ProfileMenu'
import { useSession } from '@/features/auth/useSession'
import { EMPTY_DRAFT, useCaseDetailStore } from '@/features/review/case-detail/store'
import type { StaffUser } from '@/features/auth/types'
import { renderWithRouter } from '@/test/render'

const SARI: StaffUser = {
  user_id: 'usr_sari_wulandari',
  staff_code: 'PTG-01',
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

  test('Keluar opens a confirmation dialog rather than signing out on the spot', async () => {
    await openMenu()

    await userEvent.click(screen.getByRole('menuitem', { name: /Keluar/ }))

    // Ending a session and discarding work are both undoable by nobody, so a single click is
    // too cheap for the pair.
    const dialog = await screen.findByRole('dialog')
    expect(within(dialog).getByText('Keluar dari sesi ini?')).toBeInTheDocument()
    expect(useSession.getState().user).not.toBeNull()
  })

  test('confirming in the dialog clears the session', async () => {
    await openMenu()
    await userEvent.click(screen.getByRole('menuitem', { name: /Keluar/ }))

    const dialog = await screen.findByRole('dialog')
    await userEvent.click(within(dialog).getByRole('button', { name: 'Keluar' }))

    expect(useSession.getState().user).toBeNull()
  })

  test('Batal closes the dialog and leaves the session alone', async () => {
    await openMenu()
    await userEvent.click(screen.getByRole('menuitem', { name: /Keluar/ }))

    const dialog = await screen.findByRole('dialog')
    await userEvent.click(within(dialog).getByRole('button', { name: 'Batal' }))

    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
    expect(useSession.getState().user).not.toBeNull()
  })

  test('Escape dismisses the dialog without signing out', async () => {
    await openMenu()
    await userEvent.click(screen.getByRole('menuitem', { name: /Keluar/ }))
    await screen.findByRole('dialog')

    await userEvent.keyboard('{Escape}')

    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
    expect(useSession.getState().user).not.toBeNull()
  })

  test('with an unsaved draft the dialog names what is about to be lost', async () => {
    useCaseDetailStore.setState({
      drafts: { case_1: { ...EMPTY_DRAFT, structuredReason: 'Bukti belum dilampirkan.' } },
    })
    await openMenu()
    await userEvent.click(screen.getByRole('menuitem', { name: /Keluar/ }))

    const dialog = await screen.findByRole('dialog')
    // `store.ts` keeps drafts alive so a refused save costs nothing; a silent sign-out would
    // undo that from the other direction, so the dialog says so instead of repeating itself.
    expect(within(dialog).getByText(/belum tersimpan/)).toBeInTheDocument()
    expect(within(dialog).getByRole('button', { name: 'Keluar dan buang draf' })).toBeInTheDocument()

    await userEvent.click(within(dialog).getByRole('button', { name: 'Keluar dan buang draf' }))
    expect(useSession.getState().user).toBeNull()
  })

  test('a draft that only pre-ticked itself is not called unsaved work', async () => {
    // `evidenceSeeded` is the system's doing, not the reviewer's — naming it would cry wolf.
    useCaseDetailStore.setState({ drafts: { case_1: { ...EMPTY_DRAFT, evidenceSeeded: true } } })
    await openMenu()
    await userEvent.click(screen.getByRole('menuitem', { name: /Keluar/ }))

    const dialog = await screen.findByRole('dialog')
    expect(within(dialog).queryByText(/belum tersimpan/)).not.toBeInTheDocument()
    expect(within(dialog).getByRole('button', { name: 'Keluar' })).toBeInTheDocument()
  })
})

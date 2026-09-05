import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, test } from 'vitest'

import { AppSidebar } from '@/components/layouts/AppSidebar'
import { useSession } from '@/features/auth/useSession'
import type { Role, StaffUser } from '@/features/auth/types'
import { useSidebarCollapsed } from '@/modules/sidebar/useSidebarCollapsed'
import { renderWithRouter } from '@/test/render'

function signedInAs(role: Role): StaffUser {
  return {
    user_id: `usr_${role}`,
    staff_code: 'PTG-00',
    full_name: 'Petugas Uji',
    email: 'petugas.uji@rsud-demo.example',
    role,
    is_active: true,
    last_signed_in_at: null,
  }
}

beforeEach(() => {
  useSession.setState({ user: null })
  useSidebarCollapsed.setState({ collapsed: false })
  window.localStorage.clear()
})

describe('the sidebar renders only what the role may reach', () => {
  test('reviewer sees the three review screens', () => {
    useSession.setState({ user: signedInAs('reviewer') })
    renderWithRouter(<AppSidebar />)

    expect(screen.getByRole('link', { name: 'Antrean Review' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Ingest / Demo' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Audit & Evaluasi' })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Manajemen Pengguna' })).not.toBeInTheDocument()
  })

  test('senior reviewer sees the same three', () => {
    useSession.setState({ user: signedInAs('senior_reviewer') })
    renderWithRouter(<AppSidebar />)

    expect(screen.getAllByRole('link')).toHaveLength(3)
    expect(screen.queryByRole('link', { name: 'Manajemen Pengguna' })).not.toBeInTheDocument()
  })

  test('administrator sees only the user-management page', () => {
    useSession.setState({ user: signedInAs('admin') })
    renderWithRouter(<AppSidebar />)

    // Thin on purpose: separation of duties made visible. An administrator who could also open
    // a case would be the counterexample to the control this is here to demonstrate.
    expect(screen.getAllByRole('link')).toHaveLength(1)
    expect(screen.getByRole('link', { name: 'Manajemen Pengguna' })).toBeInTheDocument()
  })

  test('the footer names the signed-in role and does not claim authentication', () => {
    useSession.setState({ user: signedInAs('senior_reviewer') })
    renderWithRouter(<AppSidebar />)

    expect(screen.getByText(/Peninjau Senior/)).toBeInTheDocument()
    expect(screen.getByText(/bukan autentikasi/)).toBeInTheDocument()
  })
})

describe('the rail can be collapsed to icons and remembers the choice', () => {
  beforeEach(() => {
    useSession.setState({ user: signedInAs('reviewer') })
  })

  test('every page stays reachable by name when collapsed', async () => {
    renderWithRouter(<AppSidebar />)

    await userEvent.click(screen.getByRole('button', { name: 'Ciutkan sidebar' }))

    // The labels are hidden from sight, never from the accessible tree: an icon-only link
    // with no name is a link a screen reader announces as its URL.
    expect(screen.getAllByRole('link')).toHaveLength(3)
    expect(screen.getByRole('link', { name: 'Antrean Review' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Antrean Review' })).toHaveAttribute(
      'title',
      'Antrean Review',
    )
  })

  test('the toggle reports the state it controls, both ways', async () => {
    renderWithRouter(<AppSidebar />)

    const collapse = screen.getByRole('button', { name: 'Ciutkan sidebar' })
    expect(collapse).toHaveAttribute('aria-expanded', 'true')
    expect(collapse).toHaveAttribute('aria-controls', 'rail-navigasi')

    await userEvent.click(collapse)
    const expand = screen.getByRole('button', { name: 'Bentangkan sidebar' })
    expect(expand).toHaveAttribute('aria-expanded', 'false')

    await userEvent.click(expand)
    expect(screen.getByRole('button', { name: 'Ciutkan sidebar' })).toBeInTheDocument()
  })

  test('the choice survives a reload', async () => {
    renderWithRouter(<AppSidebar />)

    await userEvent.click(screen.getByRole('button', { name: 'Ciutkan sidebar' }))

    expect(window.localStorage.getItem('tilik-sidebar')).toBe('collapsed')
  })

  test('the governance note is still readable by pointing at it when collapsed', async () => {
    useSession.setState({ user: signedInAs('senior_reviewer') })
    renderWithRouter(<AppSidebar />)

    await userEvent.click(screen.getByRole('button', { name: 'Ciutkan sidebar' }))

    expect(screen.getByTitle(/bukan autentikasi/)).toBeInTheDocument()
    expect(screen.getByText(/Peninjau Senior/)).toBeInTheDocument()
  })

  test('the brand mark in the rail head is not counted as a page', () => {
    renderWithRouter(<AppSidebar />)

    expect(screen.getByRole('img', { name: 'TilikKlaim' })).toBeInTheDocument()
    expect(screen.getAllByRole('link')).toHaveLength(3)
  })
})

import { screen } from '@testing-library/react'
import { beforeEach, describe, expect, test } from 'vitest'

import { AppSidebar } from '@/components/layouts/AppSidebar'
import { useSession } from '@/features/auth/useSession'
import type { Role, StaffUser } from '@/features/auth/types'
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

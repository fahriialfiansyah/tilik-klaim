import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, test } from 'vitest'

import { RequireSession } from '@/features/auth/components/RequireSession'
import { useSession } from '@/features/auth/useSession'
import type { Role, StaffUser } from '@/features/auth/types'

function signedInAs(role: Role): StaffUser {
  return {
    user_id: `usr_${role}`,
    staff_token: 'PTG-00',
    full_name: 'Petugas Uji',
    email: 'petugas.uji@rsud-demo.example',
    role,
    is_active: true,
    last_signed_in_at: null,
  }
}

/** A miniature of `App.tsx`'s route tree — enough to observe where the guard sends people. */
function renderAt(route: string) {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <Routes>
        <Route path="/login" element={<p>HALAMAN MASUK</p>} />
        <Route element={<RequireSession />}>
          <Route index element={<p>ANTREAN</p>} />
          <Route path="cases/:id" element={<p>DETAIL KASUS</p>} />
          <Route path="admin/users" element={<p>MANAJEMEN PENGGUNA</p>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  )
}

beforeEach(() => {
  useSession.setState({ user: null })
})

describe('route guard', () => {
  test('no session goes to the login page', () => {
    renderAt('/')
    expect(screen.getByText('HALAMAN MASUK')).toBeInTheDocument()
  })

  test('a reviewer reaches the queue and case detail', () => {
    useSession.setState({ user: signedInAs('reviewer') })
    renderAt('/cases/case_1')
    expect(screen.getByText('DETAIL KASUS')).toBeInTheDocument()
  })

  test('an administrator asking for a case is redirected, not shown it', () => {
    useSession.setState({ user: signedInAs('admin') })
    renderAt('/cases/case_1')

    expect(screen.queryByText('DETAIL KASUS')).not.toBeInTheDocument()
    // Sent where their role works, rather than to an error page. The API refuses the request
    // either way, with a stable code — this only saves the click.
    expect(screen.getByText('MANAJEMEN PENGGUNA')).toBeInTheDocument()
  })

  test('a reviewer asking for user management is redirected to the queue', () => {
    useSession.setState({ user: signedInAs('reviewer') })
    renderAt('/admin/users')

    expect(screen.queryByText('MANAJEMEN PENGGUNA')).not.toBeInTheDocument()
    expect(screen.getByText('ANTREAN')).toBeInTheDocument()
  })

  test('a senior reviewer is refused user management too', () => {
    useSession.setState({ user: signedInAs('senior_reviewer') })
    renderAt('/admin/users')
    expect(screen.getByText('ANTREAN')).toBeInTheDocument()
  })
})

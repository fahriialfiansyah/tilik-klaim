import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest'

import { DEMO_ACCOUNTS, credentialLine } from '@/features/auth/accounts'
import { SignInForm } from '@/features/auth/components/SignInForm'
import { MATRIX_COLUMNS } from '@/features/auth/matrix'
import { useSession } from '@/features/auth/useSession'
import { renderWithRouter } from '@/test/render'

import formSource from './SignInForm?raw'
import matrixSource from './RoleMatrix?raw'
import textureSource from './ClaimTexture?raw'
import menuSource from './ProfileMenu?raw'
import pageSource from '../../../pages/login/LoginPage?raw'

const SOURCES: Record<string, string> = {
  'SignInForm.tsx': formSource,
  'RoleMatrix.tsx': matrixSource,
  'ClaimTexture.tsx': textureSource,
  'ProfileMenu.tsx': menuSource,
  'LoginPage.tsx': pageSource,
}

const [SARI, BUDI, RINA] = DEMO_ACCOUNTS

function rowFor(fullName: string): HTMLElement {
  return screen.getByRole('row', { name: new RegExp(fullName) })
}

beforeEach(() => {
  useSession.setState({ user: null })
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('the matrix as the sign-in control', () => {
  test('opens with the reviewer chosen and both fields already filled', () => {
    renderWithRouter(<SignInForm />)

    expect(screen.getByLabelText('Email petugas')).toHaveValue(SARI.email)
    expect(screen.getByLabelText('Kode demo')).toHaveValue(SARI.passcode)
    expect(screen.getByRole('button', { name: /Masuk sebagai Peninjau$/ })).toBeEnabled()
  })

  test('choosing another row rewrites both fields and the button names that role', async () => {
    renderWithRouter(<SignInForm />)

    await userEvent.click(within(rowFor(BUDI.fullName)).getByRole('radio'))

    expect(screen.getByLabelText('Email petugas')).toHaveValue(BUDI.email)
    expect(screen.getByLabelText('Kode demo')).toHaveValue(BUDI.passcode)
    // The button says who you are about to become, so a wrong row is visible before it is pressed.
    expect(
      screen.getByRole('button', { name: 'Masuk sebagai Peninjau Senior' }),
    ).toBeInTheDocument()
  })

  test('the three personas are one radio group, so arrow keys move between them', async () => {
    renderWithRouter(<SignInForm />)
    const radios = screen.getAllByRole('radio')
    expect(radios).toHaveLength(3)

    radios[0].focus()
    await userEvent.keyboard('{ArrowDown}')

    expect(radios[1]).toBeChecked()
    expect(screen.getByLabelText('Email petugas')).toHaveValue(BUDI.email)
  })

  test('every cell states Boleh or Tidak in words, never colour alone', () => {
    renderWithRouter(<SignInForm />)
    const cells = within(rowFor(RINA.fullName)).getAllByText(/Boleh|Tidak/)
    expect(cells).toHaveLength(MATRIX_COLUMNS.length)
  })

  test('the administrator row is refused every reviewing column', () => {
    renderWithRouter(<SignInForm />)
    const row = rowFor(RINA.fullName)
    // Separation of duties, readable on the screen before anyone signs in.
    expect(within(row).getAllByText('Tidak')).toHaveLength(MATRIX_COLUMNS.length - 1)
    expect(within(row).getAllByText('Boleh')).toHaveLength(1)
  })

  test('the reviewer may not reopen a dismissed case, and the senior may', () => {
    renderWithRouter(<SignInForm />)
    const columnIndex = MATRIX_COLUMNS.findIndex((c) => c.key === 'REOPEN_DISMISSED_CASE')

    const reviewerCells = within(rowFor(SARI.fullName)).getAllByRole('cell')
    const seniorCells = within(rowFor(BUDI.fullName)).getAllByRole('cell')

    expect(reviewerCells[columnIndex]).toHaveTextContent('Tidak')
    expect(seniorCells[columnIndex]).toHaveTextContent('Boleh')
  })

  test('submit is disabled when a field is cleared, and says why', async () => {
    renderWithRouter(<SignInForm />)

    await userEvent.clear(screen.getByLabelText('Kode demo'))

    expect(screen.getByRole('button', { name: /Masuk sebagai/ })).toBeDisabled()
    expect(screen.getByText('Isi email dan kode demo terlebih dahulu.')).toBeInTheDocument()
  })

  test('the fields stay editable — the matrix is a shortcut, not the control', async () => {
    renderWithRouter(<SignInForm />)

    await userEvent.clear(screen.getByLabelText('Email petugas'))
    await userEvent.type(screen.getByLabelText('Email petugas'), 'lain@rsud-demo.example')

    expect(screen.getByLabelText('Email petugas')).toHaveValue('lain@rsud-demo.example')
    expect(screen.getByRole('button', { name: /Masuk sebagai/ })).toBeEnabled()
  })

  test('the passcode field is not masked, because the value is printed on the page', () => {
    renderWithRouter(<SignInForm />)
    expect(screen.getByLabelText('Kode demo')).toHaveAttribute('type', 'text')
  })

  test('a refused sign-in is reported without losing what was typed', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ code: 'SESSION_INVALID_CREDENTIALS', detail: 'tidak cocok' }), {
        status: 401,
        headers: { 'content-type': 'application/json' },
      }),
    )
    renderWithRouter(<SignInForm />)

    await userEvent.click(screen.getByRole('button', { name: /Masuk sebagai/ }))

    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('tidak cocok'))
    expect(screen.getByLabelText('Email petugas')).toHaveValue(SARI.email)
    expect(useSession.getState().user).toBeNull()
  })

  test('a deactivated account is told apart from a wrong passcode', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({ code: 'SESSION_ACCOUNT_DEACTIVATED', detail: 'Akun PTG-01 dinonaktifkan' }),
        { status: 403, headers: { 'content-type': 'application/json' } },
      ),
    )
    renderWithRouter(<SignInForm />)

    await userEvent.click(screen.getByRole('button', { name: /Masuk sebagai/ }))

    // The credentials were right, so "salah" would send them hunting for a typo that is not there.
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Akun nonaktif'))
  })

  test('Salin reports success only when the clipboard write resolved', async () => {
    const writeText = vi.fn(() => Promise.resolve())
    Object.defineProperty(navigator, 'clipboard', { value: { writeText }, configurable: true })
    renderWithRouter(<SignInForm />)

    await userEvent.click(screen.getByRole('button', { name: 'Salin kredensial' }))

    expect(writeText).toHaveBeenCalledWith(credentialLine(SARI))
    await waitFor(() =>
      expect(screen.getByRole('button', { name: 'Tersalin' })).toBeInTheDocument(),
    )
  })

  test('a refused clipboard write never reports "Tersalin"', async () => {
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText: vi.fn(() => Promise.reject(new Error('denied'))) },
      configurable: true,
    })
    renderWithRouter(<SignInForm />)

    await userEvent.click(screen.getByRole('button', { name: 'Salin kredensial' }))

    expect(screen.queryByRole('button', { name: 'Tersalin' })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Salin kredensial' })).toBeInTheDocument()
  })

  test('Salin copies the row that is chosen, not the one it opened with', async () => {
    const writeText = vi.fn(() => Promise.resolve())
    Object.defineProperty(navigator, 'clipboard', { value: { writeText }, configurable: true })
    renderWithRouter(<SignInForm />)

    await userEvent.click(within(rowFor(RINA.fullName)).getByRole('radio'))
    await userEvent.click(screen.getByRole('button', { name: 'Salin kredensial' }))

    expect(writeText).toHaveBeenCalledWith(credentialLine(RINA))
  })

  test('no icon on the login page is a robot or a sparkle', () => {
    for (const [file, source] of Object.entries(SOURCES)) {
      expect(source, file).not.toMatch(/\b(Bot|Sparkles?|Brain|Wand|Robot)\b/)
    }
  })

  test('the page never claims to secure anything', () => {
    // ADR-0006's first kill criterion is this page reading as a security claim.
    expect(pageSource).toMatch(/tidak mengamankan apa pun/)
    expect(pageSource).toMatch(/bukan produk atau layanan resmi BPJS Kesehatan/i)
    expect(pageSource).not.toMatch(/\b(aman|terenkripsi|terlindungi|secure)\b/i)
  })
})

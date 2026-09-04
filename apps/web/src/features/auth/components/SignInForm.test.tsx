import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest'

import { DEMO_ACCOUNTS, credentialLine } from '@/features/auth/accounts'
import { SignInForm } from '@/features/auth/components/SignInForm'
import { useSession } from '@/features/auth/useSession'
import { renderWithRouter } from '@/test/render'

import brandSource from './BrandPanel?raw'
import cardsSource from './AccountCards?raw'
import formSource from './SignInForm?raw'
import menuSource from './ProfileMenu?raw'
import pageSource from '../../../pages/login/LoginPage?raw'

const SOURCES: Record<string, string> = {
  'BrandPanel.tsx': brandSource,
  'AccountCards.tsx': cardsSource,
  'SignInForm.tsx': formSource,
  'ProfileMenu.tsx': menuSource,
  'LoginPage.tsx': pageSource,
}

const SARI = DEMO_ACCOUNTS[0]

function stubClipboard(resolves: boolean) {
  const writeText = vi.fn(() =>
    resolves ? Promise.resolve() : Promise.reject(new Error('denied')),
  )
  Object.defineProperty(navigator, 'clipboard', { value: { writeText }, configurable: true })
  return writeText
}

/** The card for one demo account, found by the name printed on it. */
function cardFor(fullName: string): HTMLElement {
  const card = screen.getByText(fullName).closest('li')
  expect(card, `no account card for ${fullName}`).not.toBeNull()
  return card as HTMLElement
}

beforeEach(() => {
  useSession.setState({ user: null })
})

afterEach(() => {
  vi.restoreAllMocks()
  vi.unstubAllGlobals()
})

describe('sign-in form', () => {
  test('submit is disabled until both fields are filled, and says why', async () => {
    renderWithRouter(<SignInForm />)

    expect(screen.getByRole('button', { name: 'Masuk' })).toBeDisabled()
    expect(screen.getByText('Isi email dan kode demo terlebih dahulu.')).toBeInTheDocument()

    await userEvent.type(screen.getByLabelText('Email petugas'), SARI.email)
    expect(screen.getByRole('button', { name: 'Masuk' })).toBeDisabled()

    await userEvent.type(screen.getByLabelText('Kode demo'), SARI.passcode)
    expect(screen.getByRole('button', { name: 'Masuk' })).toBeEnabled()
  })

  test('Pakai fills both fields and moves focus to submit', async () => {
    renderWithRouter(<SignInForm />)

    const budi = DEMO_ACCOUNTS[1]
    const card = cardFor(budi.fullName)
    await userEvent.click(within(card).getByRole('button', { name: 'Pakai' }))

    expect(screen.getByLabelText('Email petugas')).toHaveValue(budi.email)
    expect(screen.getByLabelText('Kode demo')).toHaveValue(budi.passcode)
    // One click and Enter is the whole of a persona switch mid-demo.
    expect(screen.getByRole('button', { name: 'Masuk' })).toHaveFocus()
  })

  test('Salin reports success only when the clipboard write resolved', async () => {
    const writeText = stubClipboard(true)
    renderWithRouter(<SignInForm />)

    const card = cardFor(SARI.fullName)
    await userEvent.click(within(card).getByRole('button', { name: 'Salin' }))

    expect(writeText).toHaveBeenCalledWith(credentialLine(SARI))
    await waitFor(() =>
      expect(within(card).getByRole('button', { name: 'Tersalin' })).toBeInTheDocument(),
    )
  })

  test('a refused clipboard write never reports "Tersalin"', async () => {
    stubClipboard(false)
    renderWithRouter(<SignInForm />)

    const card = cardFor(SARI.fullName)
    await userEvent.click(within(card).getByRole('button', { name: 'Salin' }))

    // The credentials stay on screen and selectable, so a failed copy costs nothing — but a
    // false "tersalin" would cost the demo a confused pause.
    expect(within(card).queryByRole('button', { name: 'Tersalin' })).not.toBeInTheDocument()
    expect(within(card).getByRole('button', { name: 'Salin' })).toBeInTheDocument()
  })

  test('the page states plainly that it is not authentication', () => {
    renderWithRouter(<SignInForm />)
    expect(screen.getByText(/memilih peran/)).toBeInTheDocument()
    expect(screen.getByText(/tidak mengamankan apa pun/)).toBeInTheDocument()
  })

  test('the passcode field is not masked, because the value is printed on the page', () => {
    renderWithRouter(<SignInForm />)
    expect(screen.getByLabelText('Kode demo')).toHaveAttribute('type', 'text')
  })

  test('no icon on the login page or in the profile menu is a robot or a sparkle', () => {
    for (const [file, source] of Object.entries(SOURCES)) {
      expect(source, file).not.toMatch(/\b(Bot|Sparkles?|Brain|Wand|Robot)\b/)
    }
  })
})

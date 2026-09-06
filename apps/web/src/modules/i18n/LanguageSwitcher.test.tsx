import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, test } from 'vitest'

import { LanguageSwitcher } from '@/modules/i18n/LanguageSwitcher'
import i18n, { STORAGE_KEY } from '@/modules/i18n/config'
import { LOCALE_NAMES } from '@/modules/i18n/locales'
import { renderWithRouter } from '@/test/render'

afterEach(() => {
  window.localStorage.removeItem(STORAGE_KEY)
})

async function openMenu() {
  await userEvent.click(screen.getByRole('button', { name: /Bahasa|language/i }))
  return screen.getByRole('menu')
}

describe('the language switch in the header', () => {
  test('shows the language currently in use, not the one it would switch to', () => {
    // With two languages there is no arrow to disambiguate, so a trigger naming its destination
    // reads as "you are in EN" to half the people who see it.
    renderWithRouter(<LanguageSwitcher />)
    expect(screen.getByRole('button')).toHaveTextContent(LOCALE_NAMES.id.short)
  })

  test('names every language in its own language', async () => {
    // Someone who cannot read the surrounding screen has to be able to find their way out of it.
    renderWithRouter(<LanguageSwitcher />)
    const menu = await openMenu()
    expect(within(menu).getByText('Bahasa Indonesia')).toBeInTheDocument()
    expect(within(menu).getByText('English')).toBeInTheDocument()
  })

  test('announces which language is live, in words rather than a tick alone', async () => {
    renderWithRouter(<LanguageSwitcher />)
    const menu = await openMenu()
    const options = within(menu).getAllByRole('menuitemradio')
    expect(options).toHaveLength(2)
    expect(options.filter((option) => option.getAttribute('aria-checked') === 'true')).toHaveLength(
      1,
    )
  })

  test('switching changes the language and the trigger follows', async () => {
    renderWithRouter(<LanguageSwitcher />)
    await openMenu()
    await userEvent.click(screen.getByRole('menuitemradio', { name: /English/ }))

    await waitFor(() => expect(i18n.language).toBe('en'))
    expect(screen.getByRole('button')).toHaveTextContent(LOCALE_NAMES.en.short)
  })

  test('the choice survives the next visit', async () => {
    // The alternative is an operator re-picking their language on every page load.
    renderWithRouter(<LanguageSwitcher />)
    await openMenu()
    await userEvent.click(screen.getByRole('menuitemradio', { name: /English/ }))

    await waitFor(() => expect(window.localStorage.getItem(STORAGE_KEY)).toBe('en'))
  })

  test('the document language follows the choice', async () => {
    // Screen readers pick pronunciation from `<html lang>`; Indonesian announced as English is
    // close to unlistenable.
    renderWithRouter(<LanguageSwitcher />)
    await openMenu()
    await userEvent.click(screen.getByRole('menuitemradio', { name: /English/ }))

    await waitFor(() => expect(document.documentElement.lang).toBe('en'))
  })
})

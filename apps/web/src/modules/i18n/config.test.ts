import { afterEach, describe, expect, test, vi } from 'vitest'

import { STORAGE_KEY, initialLocale } from '@/modules/i18n/config'
import { DEFAULT_LOCALE } from '@/modules/i18n/locales'

/**
 * Which language a first-time visitor gets.
 *
 * This is a product decision, not a technical one, and it is asserted because it was wrong once:
 * consulting `navigator.language` made the first load of a real screen come up in English, on a
 * machine whose owner reads Indonesian and had simply set their browser to English.
 */

afterEach(() => {
  window.localStorage.removeItem(STORAGE_KEY)
  vi.unstubAllGlobals()
})

describe('the language a visitor starts in', () => {
  test('is the working language when nothing has been chosen', () => {
    expect(initialLocale()).toBe(DEFAULT_LOCALE)
  })

  test('ignores an English browser', () => {
    // The reviewers this tool is built for read Indonesian. An OS setting made for unrelated
    // reasons is not evidence of what they want to read here.
    vi.stubGlobal('navigator', { ...window.navigator, language: 'en-US', languages: ['en-US'] })
    expect(initialLocale()).toBe(DEFAULT_LOCALE)
  })

  test('honours an explicit choice from a previous visit', () => {
    window.localStorage.setItem(STORAGE_KEY, 'en')
    expect(initialLocale()).toBe('en')
  })

  test('ignores a stored value that is not a language we speak', () => {
    window.localStorage.setItem(STORAGE_KEY, 'klingon')
    expect(initialLocale()).toBe(DEFAULT_LOCALE)
  })

  test('survives storage that throws', () => {
    // Private browsing and blocked site data both throw on read; the working language is still
    // a complete answer.
    const getItem = vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('site data blocked')
    })
    expect(initialLocale()).toBe(DEFAULT_LOCALE)
    getItem.mockRestore()
  })
})

import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, beforeEach, vi } from 'vitest'

import { initI18n } from '@/modules/i18n'
import { DEFAULT_LOCALE } from '@/modules/i18n/locales'
import i18n from '@/modules/i18n/config'

afterEach(cleanup)

// jsdom implements neither of these, and the theme store reads both at module load.
vi.stubGlobal(
  'matchMedia',
  vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
)

/**
 * Words, in every test.
 *
 * Components read their text through `useTranslation`, so a suite with no initialised instance
 * renders raw keys and every assertion about copy fails for the wrong reason. Initialising once
 * here is also what lets a test that cares about language call `i18n.changeLanguage('en')`.
 */
initI18n()

// Back to the working language between tests: a test that switches to English and does not put
// it back would silently retune every test that ran after it, in file order.
beforeEach(async () => {
  if (i18n.language !== DEFAULT_LOCALE) {
    await i18n.changeLanguage(DEFAULT_LOCALE)
  }
})

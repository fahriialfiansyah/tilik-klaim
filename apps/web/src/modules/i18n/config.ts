import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

import { DEFAULT_LOCALE, LOCALES, type Locale, isLocale } from '@/modules/i18n/locales'
import en from '@/locales/en'
import id from '@/locales/id'

export const STORAGE_KEY = 'tilik-locale'

/**
 * The operator's saved choice, and otherwise the working language.
 *
 * **`navigator.language` is deliberately not consulted.** It was, briefly, and the first load of
 * a real screen came up in English — because plenty of people in Indonesia run an
 * English-language browser on an otherwise Indonesian machine. The reviewers this tool is built
 * for read Indonesian; handing them English because of an OS setting they made for unrelated
 * reasons is a worse first impression than any language toggle can repair.
 *
 * So the browser preference is not evidence of what this product's user wants to read. Only an
 * explicit choice is, and the switch that records it sits in the header of every screen.
 */
export function initialLocale(): Locale {
  try {
    const saved = window.localStorage.getItem(STORAGE_KEY)
    if (isLocale(saved)) {
      return saved
    }
  } catch {
    // Private browsing and blocked site data both throw on read. The working language below is
    // a complete answer, so this is a fallback, not a swallowed failure.
  }
  return DEFAULT_LOCALE
}

/**
 * Resources are bundled rather than fetched.
 *
 * Both languages together are a few tens of kilobytes, and a screen that loads its words over
 * the network is a screen that can render with none of them. The one thing worse than an
 * untranslated label is a blank one.
 */
export const resources = { id, en } as const

/** Namespaces, with `common` first so it is what an untyped `useTranslation()` resolves to. */
export const NAMESPACES = Object.keys(resources.id) as readonly (keyof typeof resources.id)[]

export function initI18n(): typeof i18n {
  if (!i18n.isInitialized) {
    void i18n.use(initReactI18next).init({
      resources,
      lng: initialLocale(),
      fallbackLng: DEFAULT_LOCALE,
      supportedLngs: [...LOCALES],
      defaultNS: 'common',
      ns: NAMESPACES as string[],
      // A key that resolves to nothing must be visible in development rather than rendering an
      // empty cell that reads as "no data". `key-parity.test.ts` is what keeps it from shipping.
      returnEmptyString: false,
      interpolation: {
        // React escapes everything it renders already; escaping twice turns an apostrophe in
        // "Belum pernah" or a quoted code into `&#39;` on screen.
        escapeValue: false,
      },
    })
  }
  applyDocumentLanguage(i18n.language)
  return i18n
}

/**
 * Mirror the language onto `<html lang>`.
 *
 * Screen readers pick their pronunciation rules from it, and a page of Indonesian announced as
 * English is close to unlistenable. It is also what `:lang()` selectors and the browser's own
 * translate prompt read.
 */
export function applyDocumentLanguage(locale: string): void {
  document.documentElement.lang = isLocale(locale) ? locale : DEFAULT_LOCALE
}

export default i18n

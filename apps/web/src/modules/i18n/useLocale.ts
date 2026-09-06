import { useTranslation } from 'react-i18next'

import i18n, { STORAGE_KEY, applyDocumentLanguage } from '@/modules/i18n/config'
import { DEFAULT_LOCALE, type Locale, isLocale } from '@/modules/i18n/locales'

/**
 * The current language, and the one way to change it.
 *
 * i18next already holds this state and already re-renders every subscriber through
 * `useTranslation`, so there is no store here — a second copy in Zustand could disagree with
 * the instance actually resolving the keys, and the screen would render two languages at once.
 * What this hook adds is the two side effects a bare `changeLanguage` does not do: persisting
 * the choice, and keeping `<html lang>` truthful.
 */
export function useLocale(): {
  readonly locale: Locale
  readonly setLocale: (next: Locale) => void
} {
  const { i18n: instance } = useTranslation()
  const current = isLocale(instance.language) ? instance.language : DEFAULT_LOCALE

  return { locale: current, setLocale }
}

/** Change the language everywhere: the running app, the next visit, and the document itself. */
export function setLocale(next: Locale): void {
  void i18n.changeLanguage(next)
  applyDocumentLanguage(next)
  try {
    window.localStorage.setItem(STORAGE_KEY, next)
  } catch {
    // Persisting is a convenience; the session still runs in the chosen language.
  }
}

/**
 * The languages the app speaks.
 *
 * Indonesian is the working language: it is what the reviewers who use this tool speak, what
 * `docs/canonical/` is written in, and what the backend's reason catalog is authored in.
 * English is a second rendering of the same product — it exists so a judge, a partner, or an
 * engineer outside the team can read the screens, and it never changes what those screens say.
 */

export const LOCALES = ['id', 'en'] as const

export type Locale = (typeof LOCALES)[number]

export const DEFAULT_LOCALE: Locale = 'id'

/**
 * How each language names *itself*.
 *
 * An endonym, never a translation: someone looking for their own language scans for the word
 * they would write it with, and "Bahasa Indonesia" in an English menu is the entry an
 * Indonesian speaker finds instantly. The short form is what fits the header button.
 */
export const LOCALE_NAMES: Readonly<Record<Locale, { readonly full: string; readonly short: string }>> =
  {
    id: { full: 'Bahasa Indonesia', short: 'ID' },
    en: { full: 'English', short: 'EN' },
  }

export function isLocale(value: unknown): value is Locale {
  return typeof value === 'string' && (LOCALES as readonly string[]).includes(value)
}

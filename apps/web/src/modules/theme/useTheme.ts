import { create } from 'zustand'

export type Theme = 'light' | 'dark'

const STORAGE_KEY = 'tilik-theme'

/** Reads the operator's saved choice; falls back to the OS preference. */
function initialTheme(): Theme {
  try {
    const saved = window.localStorage.getItem(STORAGE_KEY)
    if (saved === 'light' || saved === 'dark') {
      return saved
    }
  } catch {
    // Private browsing and blocked site data both throw here. The OS preference
    // below is a complete answer, so this is a fallback, not a swallowed failure.
  }
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

/**
 * `data-theme` on the document element is what `tokens.css` keys on. Setting it explicitly
 * — rather than leaving the media query to decide — is what lets the operator override the
 * OS preference, which matters in a reading-heavy tool used all day.
 */
function applyTheme(theme: Theme): void {
  document.documentElement.dataset.theme = theme
  try {
    window.localStorage.setItem(STORAGE_KEY, theme)
  } catch {
    // Persisting is a convenience; the session still renders in the chosen theme.
  }
}

type ThemeStore = {
  readonly theme: Theme
  readonly toggle: () => void
}

export const useTheme = create<ThemeStore>((set, get) => ({
  theme: initialTheme(),
  toggle: () => {
    const next: Theme = get().theme === 'dark' ? 'light' : 'dark'
    applyTheme(next)
    set({ theme: next })
  },
}))

/** Called once at start-up so the first paint matches the stored choice. */
export function initTheme(): void {
  applyTheme(useTheme.getState().theme)
}

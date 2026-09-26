import { create } from 'zustand'

export type Theme = 'light' | 'dark'

const STORAGE_KEY = 'tilik-theme'

/**
 * Light unless the operator chose dark themselves. The OS preference is deliberately not
 * consulted: reviewers read white claim documents in lit offices, and the demo runs on a
 * projector, where a dark screen washes out. Dark stays one click away in the header.
 */
const DEFAULT_THEME: Theme = 'light'

/** Reads the operator's saved choice; falls back to the light default. */
function initialTheme(): Theme {
  try {
    const saved = window.localStorage.getItem(STORAGE_KEY)
    if (saved === 'light' || saved === 'dark') {
      return saved
    }
  } catch {
    // Private browsing and blocked site data both throw here. The default below is a
    // complete answer, so this is a fallback, not a swallowed failure.
  }
  return DEFAULT_THEME
}

/**
 * `data-theme` on the document element is what `tokens.css` keys on. It is always set
 * explicitly, so the theme on screen is the one this store holds and never the OS's.
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

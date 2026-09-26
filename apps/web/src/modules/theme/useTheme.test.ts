import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest'

const STORAGE_KEY = 'tilik-theme'

/** The store reads its first value at module load, so every case imports a fresh copy. */
async function loadThemeModule() {
  vi.resetModules()
  return import('@/modules/theme/useTheme')
}

function preferDarkOs(): void {
  vi.stubGlobal(
    'matchMedia',
    vi.fn().mockImplementation((query: string) => ({
      matches: query === '(prefers-color-scheme: dark)',
      media: query,
      onchange: null,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  )
}

describe('useTheme', () => {
  beforeEach(() => {
    window.localStorage.clear()
    delete document.documentElement.dataset.theme
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  test('starts light when nothing is saved, even on an OS set to dark', async () => {
    preferDarkOs()

    const { useTheme } = await loadThemeModule()

    expect(useTheme.getState().theme).toBe('light')
  })

  test('keeps a dark theme the operator chose earlier', async () => {
    preferDarkOs()
    window.localStorage.setItem(STORAGE_KEY, 'dark')

    const { useTheme } = await loadThemeModule()

    expect(useTheme.getState().theme).toBe('dark')
  })

  test('ignores a saved value it does not recognise and starts light', async () => {
    window.localStorage.setItem(STORAGE_KEY, 'sepia')

    const { useTheme } = await loadThemeModule()

    expect(useTheme.getState().theme).toBe('light')
  })

  test('marks the document light at start-up, so the stylesheet never falls back to the OS', async () => {
    preferDarkOs()

    const { initTheme } = await loadThemeModule()
    initTheme()

    expect(document.documentElement.dataset.theme).toBe('light')
  })

  test('toggling switches the document and remembers the choice', async () => {
    const { initTheme, useTheme } = await loadThemeModule()
    initTheme()

    useTheme.getState().toggle()

    expect(useTheme.getState().theme).toBe('dark')
    expect(document.documentElement.dataset.theme).toBe('dark')
    expect(window.localStorage.getItem(STORAGE_KEY)).toBe('dark')
  })
})

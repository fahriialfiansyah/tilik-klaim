import { useTheme } from '@/modules/theme/useTheme'

/**
 * Light/dark switch in the app header. Both themes are token-driven and both clear AA on
 * every status band, so neither is a degraded mode.
 *
 * Icon only: a sun in the light theme, a moon in the dark one. The word that used to sit beside
 * it ("Terang" / "Gelap") is gone from the surface but **not** from the accessible name — a
 * control whose meaning lives only in a picture is a control a screen reader cannot describe.
 * `aria-pressed` carries the state, `aria-label` names the act, and `title` gives a pointer the
 * same sentence.
 *
 * The icons are drawn here rather than imported so the stroke weight matches the product mark
 * (`TilikKlaimMark`), which is the only other line-work in the header.
 */
export function ThemeToggle() {
  const theme = useTheme((state) => state.theme)
  const toggle = useTheme((state) => state.toggle)
  const isDark = theme === 'dark'

  return (
    <button
      type="button"
      onClick={toggle}
      aria-pressed={isDark}
      aria-label={isDark ? 'Tema gelap aktif. Ganti ke terang.' : 'Tema terang aktif. Ganti ke gelap.'}
      title="Ganti tema"
      className="flex size-8 items-center justify-center rounded-full border border-ink-inv/12 bg-ink-inv/6 text-ink-inv transition-colors hover:bg-ink-inv/14 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink-inv"
    >
      {isDark ? <MoonIcon /> : <SunIcon />}
    </button>
  )
}

/** A crescent, cut by a second circle rather than drawn as a path — it stays true at 16 px. */
function MoonIcon() {
  return (
    <svg
      aria-hidden
      viewBox="0 0 24 24"
      className="size-[17px]"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M20 14.2A8.4 8.4 0 0 1 9.8 4 8.4 8.4 0 1 0 20 14.2Z" />
    </svg>
  )
}

/** Disc plus eight rays. Rays are separate strokes so none of them touches the disc. */
function SunIcon() {
  return (
    <svg
      aria-hidden
      viewBox="0 0 24 24"
      className="size-[17px]"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2.5v2M12 19.5v2M4.6 4.6l1.4 1.4M18 18l1.4 1.4M2.5 12h2M19.5 12h2M4.6 19.4 6 18M18 6l1.4-1.4" />
    </svg>
  )
}

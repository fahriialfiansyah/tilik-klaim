import { useTheme } from '@/modules/theme/useTheme'

/**
 * Light/dark switch in the app header. Both themes are token-driven and both clear AA on
 * every status band, so neither is a degraded mode.
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
      title="Ganti tema"
      className="flex items-center gap-[7px] rounded-full border border-ink-inv/12 bg-ink-inv/6 px-[10px] py-[6px] text-meta font-medium text-ink-inv transition-colors hover:bg-ink-inv/14"
    >
      <span
        aria-hidden
        className={`relative block h-4 w-7 rounded-full transition-colors ${
          isDark ? 'bg-brand' : 'bg-ink-inv/24'
        }`}
      >
        <span
          className={`absolute top-[2px] size-3 rounded-full bg-ink-inv transition-[left] duration-200 ${
            isDark ? 'left-[14px]' : 'left-[2px]'
          }`}
        />
      </span>
      {isDark ? 'Gelap' : 'Terang'}
    </button>
  )
}

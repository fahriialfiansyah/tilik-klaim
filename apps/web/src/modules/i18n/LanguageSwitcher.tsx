import { Check, Languages } from 'lucide-react'
import { useTranslation } from 'react-i18next'

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { cn } from '@/lib/utils'
import { LOCALES, LOCALE_NAMES } from '@/modules/i18n/locales'
import { useLocale } from '@/modules/i18n/useLocale'

/**
 * Language switch in the app header, beside the theme switch.
 *
 * The two belong together: both change how the app is *presented* and neither touches a case,
 * a disposition, or a score. Putting the language anywhere else — a settings page, a profile
 * submenu — would hide it from the reader most likely to need it, who by definition cannot read
 * the menu they would have to navigate to find it.
 *
 * The trigger shows the **current** language's own short code rather than the one it would
 * switch to. A control that names its destination reads as "you are in EN" to half of the
 * people who see it, and with only two languages there is no arrow to disambiguate it.
 *
 * Each entry is written in its own language and never translated, so someone who cannot read
 * the surrounding screen can still find their way out of it.
 */
export function LanguageSwitcher() {
  const { t } = useTranslation('common')
  const { locale, setLocale } = useLocale()

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        aria-label={t('language.switch', { language: LOCALE_NAMES[locale].full })}
        title={t('language.title')}
        className="flex h-8 items-center gap-[6px] rounded-full border border-ink-inv/12 bg-ink-inv/6 px-[10px] text-ink-inv transition-colors hover:bg-ink-inv/14 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink-inv"
      >
        <Languages aria-hidden className="size-[15px]" />
        <span data-numeric className="font-mono text-meta font-semibold">
          {LOCALE_NAMES[locale].short}
        </span>
      </DropdownMenuTrigger>

      <DropdownMenuContent aria-label={t('language.menu')} className="min-w-[200px]">
        <DropdownMenuLabel className="text-meta text-ink-3">
          {t('language.heading')}
        </DropdownMenuLabel>

        <DropdownMenuSeparator />

        {LOCALES.map((candidate) => {
          const active = candidate === locale
          return (
            <DropdownMenuItem
              key={candidate}
              onSelect={() => setLocale(candidate)}
              /*
               * `aria-checked` on a `menuitemradio`, not `aria-selected`: this is a choice
               * between mutually exclusive options, and it is the only thing announcing which
               * one is live — the tick beside it is `aria-hidden` decoration.
               */
              role="menuitemradio"
              aria-checked={active}
              className={cn('justify-between', active && 'text-brand')}
            >
              <span className={cn(active && 'font-semibold')}>
                {LOCALE_NAMES[candidate].full}
              </span>
              {active ? <Check aria-hidden className="size-4 shrink-0" /> : null}
            </DropdownMenuItem>
          )
        })}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

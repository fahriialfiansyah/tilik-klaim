import { NavLink } from 'react-router-dom'

import { PerfectScrollArea } from '@/components/wrappers/PerfectScrollArea'
import { NAVIGABLE_MENU } from '@/config/menu/app-menu'
import { cn } from '@/lib/utils'

/**
 * Primary navigation (G2).
 *
 * Entries come from `src/config/menu/app-menu.ts` and nowhere else — the architecture rules
 * make that file the source of truth so a route can never drift from the menu that reaches it.
 */
export function AppSidebar() {
  return (
    <nav
      aria-label="Navigasi utama"
      className="flex w-[220px] shrink-0 flex-col border-r border-line bg-rail"
    >
      <PerfectScrollArea className="flex-1 px-2 py-[14px]">
        <p className="mx-2 mb-2 font-mono text-micro font-semibold tracking-label text-ink-3">
          MENU
        </p>
        <ul className="flex flex-col gap-[3px]">
          {NAVIGABLE_MENU.map((entry) => (
            <li key={entry.id}>
              <NavLink
                to={entry.route}
                end={entry.route === '/'}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-[11px] rounded-md border px-[10px] py-[9px] font-medium transition-colors',
                    isActive
                      ? 'border-brand-line bg-brand-soft text-brand'
                      : 'border-transparent text-ink hover:bg-accent',
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    {/*
                      Three uneven bars — the mark's motif at nav scale. Decorative, so it is
                      hidden from assistive tech; the label beside it carries the meaning.
                    */}
                    <span aria-hidden className="flex w-4 shrink-0 flex-col gap-[2.5px]">
                      <span
                        className={cn(
                          'block h-[2px] w-3 rounded-sm',
                          isActive ? 'bg-brand' : 'bg-ink-3',
                        )}
                      />
                      <span
                        className={cn(
                          'block h-[2px] w-4 rounded-sm',
                          isActive ? 'bg-notice' : 'bg-ink-3',
                        )}
                      />
                      <span
                        className={cn(
                          'block h-[2px] w-2 rounded-sm',
                          isActive ? 'bg-brand' : 'bg-ink-3',
                        )}
                      />
                    </span>
                    <span className="min-w-0 flex-1 truncate">{entry.label}</span>
                  </>
                )}
              </NavLink>
            </li>
          ))}
        </ul>
      </PerfectScrollArea>

      <p className="border-t border-line px-[10px] py-3 text-meta leading-[1.45] text-ink-3">
        Tidak ada halaman login. Peran disimulasikan untuk demo.
      </p>
    </nav>
  )
}

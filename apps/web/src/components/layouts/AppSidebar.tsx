import { NavLink } from 'react-router-dom'

import { MENU_ICONS } from '@/components/layouts/MenuIcons'
import { PerfectScrollArea } from '@/components/wrappers/PerfectScrollArea'
import { menuForRole } from '@/config/menu/app-menu'
import { ROLE_LABEL } from '@/features/auth/labels'
import { useSession } from '@/features/auth/useSession'
import { cn } from '@/lib/utils'

/**
 * Primary navigation (G2).
 *
 * Entries come from `src/config/menu/app-menu.ts` and nowhere else — the architecture rules
 * make that file the source of truth so a route can never drift from the menu that reaches it.
 *
 * Since ADR-0006 the list is filtered by the signed-in role, which is what makes separation of
 * duties visible: an administrator's sidebar has one entry, and that is the point rather than
 * an oversight. **Filtering is a courtesy, not the control** — the server refuses every hidden
 * route with a stable error code, and `apps/backend/tests/test_access.py` asserts it.
 */
export function AppSidebar() {
  const user = useSession((state) => state.user)
  const entries = user ? menuForRole(user.role) : []

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
          {entries.map((entry) => {
            // One drawn mark per page, from `MenuIcons.tsx`. The three uneven bars that used to
            // sit here were the same shape on every entry — decoration rather than a signpost.
            const Icon = MENU_ICONS[entry.id]
            return (
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
                      {Icon ? (
                        <Icon
                          className={cn(
                            'size-[18px] shrink-0',
                            isActive ? 'text-brand' : 'text-ink-3',
                          )}
                        />
                      ) : null}
                      <span className="min-w-0 flex-1 truncate">{entry.label}</span>
                    </>
                  )}
                </NavLink>
              </li>
            )
          })}
        </ul>
      </PerfectScrollArea>

      <p className="border-t border-line px-[10px] py-3 text-meta leading-[1.45] text-ink-3">
        {user ? (
          <>
            Masuk sebagai <span className="font-medium text-ink-2">{ROLE_LABEL[user.role]}</span>.
            Peran disimulasikan — bukan autentikasi.
          </>
        ) : (
          'Peran disimulasikan untuk demo — bukan autentikasi.'
        )}
      </p>
    </nav>
  )
}

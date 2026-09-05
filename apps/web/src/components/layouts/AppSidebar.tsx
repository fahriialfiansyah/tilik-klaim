import { ArrowLeft, ArrowRight, Info } from 'lucide-react'
import { NavLink } from 'react-router-dom'

import { TilikKlaimMark } from '@/components/brand/TilikKlaimMark'
import { MENU_ICONS } from '@/components/layouts/MenuIcons'
import { PerfectScrollArea } from '@/components/wrappers/PerfectScrollArea'
import { menuForRole } from '@/config/menu/app-menu'
import { ROLE_LABEL } from '@/features/auth/labels'
import { useSession } from '@/features/auth/useSession'
import { cn } from '@/lib/utils'
import { useSidebarCollapsed } from '@/modules/sidebar/useSidebarCollapsed'

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
 *
 * The rail also owns the product mark. It used to sit in the full-width header, which meant the
 * wordmark could never follow the rail when it was collapsed — the mark belongs to the column
 * whose width it announces. The brand block keeps `bg-head` and the exact height of the header,
 * so the dark band still reads as one strip across the top of the app.
 */
export function AppSidebar() {
  const user = useSession((state) => state.user)
  const collapsed = useSidebarCollapsed((state) => state.collapsed)
  const toggle = useSidebarCollapsed((state) => state.toggle)
  const entries = user ? menuForRole(user.role) : []

  return (
    <nav
      id="rail-navigasi"
      aria-label="Navigasi utama"
      className={cn(
        'flex shrink-0 flex-col overflow-hidden transition-[width] duration-[var(--motion-layout)] ease-[var(--ease-out)]',
        collapsed ? 'w-[var(--rail-w-min)]' : 'w-[var(--rail-w)]',
      )}
    >
      {/*
        The brand block, not a link: `getAllByRole('link')` in the sidebar is a count of pages a
        role may reach, and a logo that answered to that role would quietly inflate it.
      */}
      <div
        className={cn(
          'flex h-[var(--header-h)] shrink-0 items-center gap-[10px] bg-head',
          collapsed ? 'justify-center px-0' : 'px-4',
        )}
      >
        <TilikKlaimMark className="block size-[30px] shrink-0" />
        {collapsed ? null : (
          <span className="truncate text-lead font-semibold tracking-[.11em] text-ink-inv">
            TILIKKLAIM
          </span>
        )}
      </div>

      <div className="flex min-h-0 flex-1 flex-col border-r border-line bg-rail">
        <PerfectScrollArea className={cn('flex-1 py-[14px]', collapsed ? 'px-[9px]' : 'px-2')}>
          {collapsed ? null : (
            <p className="mx-2 mb-2 font-mono text-micro font-semibold tracking-label text-ink-3">
              MENU
            </p>
          )}
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
                    // Native `title` rather than a tooltip primitive: collapsed, the icon is the
                    // only thing on screen, and the label must still be readable by pointing at it.
                    title={collapsed ? entry.label : undefined}
                    className={({ isActive }) =>
                      cn(
                        'flex items-center rounded-md border font-medium transition-colors',
                        collapsed
                          ? 'justify-center px-0 py-[9px]'
                          : 'gap-[11px] px-[10px] py-[9px]',
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
                        {/*
                          Kept in the accessible tree when collapsed, never removed: an icon-only
                          link with no name is a link a screen reader announces as its URL.
                        */}
                        <span className={cn('min-w-0 flex-1 truncate', collapsed && 'sr-only')}>
                          {entry.label}
                        </span>
                      </>
                    )}
                  </NavLink>
                </li>
              )
            })}
          </ul>
        </PerfectScrollArea>

        <button
          type="button"
          onClick={toggle}
          aria-expanded={!collapsed}
          aria-controls="rail-navigasi"
          aria-label={collapsed ? 'Bentangkan sidebar' : 'Ciutkan sidebar'}
          title={collapsed ? 'Bentangkan sidebar' : 'Ciutkan sidebar'}
          className={cn(
            'flex items-center border-t border-line py-[11px] text-meta font-medium text-ink-3 transition-colors hover:bg-accent hover:text-ink-2 focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-brand',
            collapsed ? 'justify-center px-0' : 'gap-[11px] px-[14px]',
          )}
        >
          {collapsed ? (
            <ArrowRight aria-hidden className="size-[18px] shrink-0" />
          ) : (
            <>
              <ArrowLeft aria-hidden className="size-[18px] shrink-0" />
              <span aria-hidden className="truncate">
                Ciutkan sidebar
              </span>
            </>
          )}
        </button>

        <p
          // Collapsed there is no room for the sentence, but the claim it makes — that this is a
          // simulated role and not authentication — is a governance statement, not a caption.
          // It stays in the accessible tree and stays reachable by pointing at the marker.
          title={collapsed ? noteText(user ? ROLE_LABEL[user.role] : null) : undefined}
          className={cn(
            'border-t border-line py-3 text-meta leading-[1.45] text-ink-3',
            collapsed ? 'px-0 text-center' : 'px-[10px]',
          )}
        >
          {collapsed ? <Info aria-hidden className="mx-auto size-[18px]" /> : null}
          <span className={cn(collapsed && 'sr-only')}>
            {user ? (
              <>
                Masuk sebagai <span className="font-medium text-ink-2">{ROLE_LABEL[user.role]}</span>
                . Peran disimulasikan — bukan autentikasi.
              </>
            ) : (
              'Peran disimulasikan untuk demo — bukan autentikasi.'
            )}
          </span>
        </p>
      </div>
    </nav>
  )
}

/** The same sentence the footer renders, flattened for a `title` attribute. */
function noteText(role: string | null): string {
  return role
    ? `Masuk sebagai ${role}. Peran disimulasikan — bukan autentikasi.`
    : 'Peran disimulasikan untuk demo — bukan autentikasi.'
}

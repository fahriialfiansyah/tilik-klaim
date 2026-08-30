import { NavLink, Outlet } from 'react-router-dom'

import { NAVIGABLE_MENU } from '@/config/menu/app-menu'

/**
 * App shell. Header, sidebar, and main each reserve their own layout space —
 * no z-index stacking to hide structural overlap (architecture.md § Web UI Enforcement).
 */
export function AppShell() {
  return (
    <div className="flex h-screen flex-col overflow-hidden">
      <header className="flex h-12 shrink-0 items-center justify-between border-b px-4">
        <span className="font-semibold">TilikKlaim</span>
        {/*
          Synthetic-data badge. Required on every page by
          docs/canonical/07_privacy_threat_model.md — it must not be dismissible.
        */}
        <span data-testid="synthetic-badge" className="rounded px-2 py-1 text-xs">
          DATA SINTETIK
        </span>
      </header>

      <div className="flex min-h-0 flex-1 overflow-hidden">
        <nav className="w-[220px] shrink-0 overflow-y-auto border-r p-2">
          {NAVIGABLE_MENU.map((entry) => (
            <NavLink key={entry.id} to={entry.route} className="block px-2 py-1">
              {entry.label}
            </NavLink>
          ))}
        </nav>

        <main className="flex-1 overflow-auto p-4">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

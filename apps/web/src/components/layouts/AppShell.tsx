import { Outlet } from 'react-router-dom'

import { AppHeader } from '@/components/layouts/AppHeader'
import { AppSidebar } from '@/components/layouts/AppSidebar'
import { PerfectScrollArea } from '@/components/wrappers/PerfectScrollArea'

/**
 * App shell. Header, sidebar, and main each reserve their own layout space —
 * no z-index stacking to hide structural overlap (architecture.md § Web UI Enforcement).
 */
export function AppShell() {
  return (
    <div className="flex h-screen flex-col overflow-hidden bg-background">
      <AppHeader />

      <div className="flex min-h-0 flex-1 overflow-hidden">
        <AppSidebar />

        <PerfectScrollArea className="flex-1">
          <main>
            <Outlet />
          </main>
        </PerfectScrollArea>
      </div>
    </div>
  )
}

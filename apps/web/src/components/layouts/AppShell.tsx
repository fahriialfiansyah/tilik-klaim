import { Outlet } from 'react-router-dom'

import { AppHeader } from '@/components/layouts/AppHeader'
import { AppSidebar } from '@/components/layouts/AppSidebar'
import { PerfectScrollArea } from '@/components/wrappers/PerfectScrollArea'

/**
 * App shell. Header, sidebar, and main each reserve their own layout space —
 * no z-index stacking to hide structural overlap (architecture.md § Web UI Enforcement).
 *
 * The rail is now the outer column and runs the full height, because it owns the product mark:
 * its head block sits at exactly `--header-h` beside the header, so the two together still read
 * as one dark band even though the rail underneath them can be collapsed to icons.
 */
export function AppShell() {
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <AppSidebar />

      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <AppHeader />

        <PerfectScrollArea className="flex-1">
          <main>
            <Outlet />
          </main>
        </PerfectScrollArea>
      </div>
    </div>
  )
}

import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { mayReach } from '@/config/menu/app-menu'
import { LANDING_ROUTE } from '@/features/auth/permissions'
import { useSession } from '@/features/auth/useSession'

/**
 * The gate in front of everything inside `AppShell`.
 *
 * Two redirects, and they mean different things:
 *
 * * **No session → `/login`.** Nobody is chosen yet, so there is nothing to render.
 * * **A session that may not reach this route → that role's landing page.** An administrator
 *   who types `/cases/abc` is not shown an error; they are put where their role works. The
 *   API refuses the underlying request in either case, with a stable code — this only saves
 *   them the click.
 *
 * `replace` on both, so the browser's back button does not bounce between the guard and the
 * route it refused.
 */
export function RequireSession() {
  const user = useSession((state) => state.user)
  const location = useLocation()

  if (!user) {
    return <Navigate to="/login" replace />
  }
  if (!mayReach(user.role, location.pathname)) {
    return <Navigate to={LANDING_ROUTE[user.role]} replace />
  }
  return <Outlet />
}

import { CASE_ROLES } from '@/features/auth/permissions'
import type { Role } from '@/features/auth/types'

/**
 * Navigation source of truth.
 *
 * `.claude/rules/architecture.md` requires menu entries to live here and be rendered
 * from these arrays — layout components must never hardcode their own route lists.
 * Routes and ids mirror sprint/00-app-spec.md § 1 and design/flow.json `screens[]`.
 *
 * Since ADR-0006 each entry also declares **which roles may reach it**, and the sidebar renders
 * from that. The declaration lives beside the route for the same reason the route does: a
 * permission kept somewhere else is a permission that drifts from the page it guards.
 *
 * Identifiers are English; user-facing `label` stays Indonesian.
 */
export type MenuEntry = {
  readonly id: string
  readonly label: string
  readonly route: string
  /** Shown in the sidebar. Detail routes are reachable but not navigable directly. */
  readonly navigable: boolean
  /** Roles permitted to reach this route. The server refuses the rest regardless. */
  readonly roles: readonly Role[]
}

export const APP_MENU: readonly MenuEntry[] = [
  { id: 'queue', label: 'Antrean Review', route: '/', navigable: true, roles: CASE_ROLES },
  { id: 'ingest', label: 'Ingest / Demo', route: '/ingest', navigable: true, roles: CASE_ROLES },
  {
    id: 'evaluation',
    label: 'Audit & Evaluasi',
    route: '/evaluation',
    navigable: true,
    roles: CASE_ROLES,
  },
  {
    id: 'admin-users',
    label: 'Manajemen Pengguna',
    route: '/admin/users',
    navigable: true,
    roles: ['admin'],
  },
  {
    id: 'case-detail',
    label: 'Detail Kasus',
    route: '/cases/:id',
    navigable: false,
    roles: CASE_ROLES,
  },
] as const

/** The sidebar's entries for one role. Empty is a valid answer, not a bug. */
export function menuForRole(role: Role): readonly MenuEntry[] {
  return APP_MENU.filter((entry) => entry.navigable && entry.roles.includes(role))
}

/**
 * May this role open this path?
 *
 * Matched against the menu's own routes so a new page is permitted by adding it there, not by
 * editing a second list. `/cases/:id` is matched by prefix; everything else is exact.
 */
export function mayReach(role: Role, pathname: string): boolean {
  const entry = APP_MENU.find((candidate) =>
    candidate.route.includes(':')
      ? pathname.startsWith(candidate.route.slice(0, candidate.route.indexOf(':')))
      : candidate.route === pathname,
  )
  return entry ? entry.roles.includes(role) : false
}

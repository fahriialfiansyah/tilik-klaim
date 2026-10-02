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
 * Identifiers are English, and each one **is** the entry's translation key: `id` looks up
 * `menu:<id>` in `src/locales/<locale>/menu.json`. There is no `label` field, because a label written
 * here would be a second name for a page that only ever exists in one language — the entry that
 * had one would go untranslated while every other entry followed the header switch.
 * `app-menu.test.ts` asserts every id resolves in both languages.
 */
export type MenuEntry = {
  readonly id: string
  readonly route: string
  /** Shown in the sidebar. Detail routes are reachable but not navigable directly. */
  readonly navigable: boolean
  /** Roles permitted to reach this route. The server refuses the rest regardless. */
  readonly roles: readonly Role[]
}

export const APP_MENU: readonly MenuEntry[] = [
  { id: 'queue', route: '/', navigable: true, roles: CASE_ROLES },
  // ADR-0007. Reads only what the queue and case detail already show these roles.
  { id: 'assistant', route: '/assistant', navigable: true, roles: CASE_ROLES },
  { id: 'ingest', route: '/ingest', navigable: true, roles: CASE_ROLES },
  {
    id: 'evaluation',
    route: '/evaluation',
    navigable: true,
    roles: CASE_ROLES,
  },
  {
    id: 'admin-users',
    route: '/admin/users',
    navigable: true,
    roles: ['admin'],
  },
  {
    id: 'case-detail',
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

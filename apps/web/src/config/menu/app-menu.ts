/**
 * Navigation source of truth.
 *
 * `.claude/rules/architecture.md` requires menu entries to live here and be rendered
 * from these arrays — layout components must never hardcode their own route lists.
 * Routes mirror sprint/00-app-spec.md § 1 Page Inventory.
 */
export type MenuEntry = {
  readonly id: string
  readonly label: string
  readonly route: string
  /** Shown in the sidebar. Detail routes are reachable but not navigable directly. */
  readonly navigable: boolean
}

export const APP_MENU: readonly MenuEntry[] = [
  { id: 'antrean-review', label: 'Antrean Review', route: '/', navigable: true },
  { id: 'ingest-demo', label: 'Ingest / Demo', route: '/ingest', navigable: true },
  { id: 'audit-evaluasi', label: 'Audit & Evaluasi', route: '/evaluation', navigable: true },
  { id: 'detail-kasus', label: 'Detail Kasus', route: '/cases/:id', navigable: false },
] as const

export const NAVIGABLE_MENU = APP_MENU.filter((entry) => entry.navigable)

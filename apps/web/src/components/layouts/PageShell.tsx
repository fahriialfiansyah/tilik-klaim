import type { ReactNode } from 'react'

import { cn } from '@/lib/utils'

/**
 * Widest the content column may grow before it stops following the viewport.
 *
 * Driven by what the widest widget on the page actually needs: the queue table carries nine
 * columns, most pages carry five or fewer, and the case detail runs its own two-column grid
 * that wants the whole frame.
 */
const COLUMN_WIDTHS = {
  wide: 'max-w-[1560px]',
  default: 'max-w-[1240px]',
  full: '',
} as const

type PageShellProps = {
  readonly children: ReactNode
  readonly width?: keyof typeof COLUMN_WIDTHS
  readonly className?: string
}

/**
 * The one frame every routed page sits in: 30px gutters, 26px of lead-in, and 72px of runway
 * under the last widget so the final row never ends flush against the viewport edge.
 *
 * **Do not open a scroll region here.** `AppShell` already wraps `<Outlet />` in a
 * `PerfectScrollArea`, and that is the main column's only scroller. A second one nested inside
 * it binds a `wheel` handler that calls `stopPropagation()` as soon as it is at its own scroll
 * bound — which it always is, because a page body has no bounded height to scroll within — so
 * the wheel gesture never reaches the shell and the page freezes.
 */
export function PageShell({ children, width = 'default', className }: PageShellProps) {
  return (
    <section className={cn('px-[30px] pt-[26px] pb-[72px]', COLUMN_WIDTHS[width], className)}>
      {children}
    </section>
  )
}

type PageHeaderProps = {
  /** Short all-caps kicker naming what the page is and how it is ordered or bounded. */
  readonly eyebrow: string
  readonly title: string
  readonly lede?: ReactNode
  /** Primary action, pinned to the baseline of the title block. */
  readonly action?: ReactNode
  readonly className?: string
}

/** Page title block. Eyebrow, page-size heading, lede, and at most one primary action. */
export function PageHeader({ eyebrow, title, lede, action, className }: PageHeaderProps) {
  return (
    <div className={cn('mb-[22px] flex items-end justify-between gap-6', className)}>
      <div>
        <p className="mb-[5px] font-mono text-micro font-semibold tracking-label text-ink-3">
          {eyebrow}
        </p>
        <h1 className="text-page font-semibold tracking-title text-ink">{title}</h1>
        {lede ? <p className="mt-[6px] max-w-[640px] text-ink-2 text-pretty">{lede}</p> : null}
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </div>
  )
}

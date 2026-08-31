import PerfectScrollbar from 'react-perfect-scrollbar'
import type { ReactNode } from 'react'

import { cn } from '@/lib/utils'

type PerfectScrollAreaProps = {
  readonly children: ReactNode
  readonly className?: string
  /** Set when the region scrolls sideways too, e.g. the wide queue table. */
  readonly axis?: 'y' | 'both'
}

/**
 * Adapter for `react-perfect-scrollbar`.
 *
 * `.claude/rules/architecture.md` requires every bounded scroll region — the main column,
 * drawers, panels, fixed-height lists — to go through this rather than raw `overflow-auto`,
 * so scrollbars follow the active theme. Theming lives in `src/styles/components.css`.
 *
 * The wrapper must have a bounded height for the library to measure; give the parent
 * `min-h-0` in a flex chain or the region will grow instead of scroll.
 */
export function PerfectScrollArea({ children, className, axis = 'y' }: PerfectScrollAreaProps) {
  return (
    <PerfectScrollbar
      className={cn('min-h-0', className)}
      options={{
        // Vertical-only regions must not swallow horizontal wheel gestures.
        suppressScrollX: axis === 'y',
        // Stops a nested region from scroll-chaining into the page behind it.
        wheelPropagation: false,
      }}
    >
      {children}
    </PerfectScrollbar>
  )
}

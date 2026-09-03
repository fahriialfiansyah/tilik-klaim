import { ComparisonDrawer } from '@/features/review/case-detail/components/ComparisonDrawer'
import { SourceDrawer } from '@/features/review/case-detail/components/SourceDrawer'
import { useCaseDetailStore } from '@/features/review/case-detail/store'
import type { SourceResource } from '@/features/review/case-detail/types'
import type { VersionStamp } from '@/modules/engine-version/useEngineVersion'

/**
 * Widgets 16, 23 and 24 behind one piece of state (ADR-0004 § Decision 4).
 *
 * The store holds a single `drawer` union — `none`, `source`, or `comparison` — so the two
 * drawers cannot both be open: not because a handler closes one before opening the other, but
 * because there is no value of the type in which both are open. Selecting a different reason or
 * line closes whichever is open, so the drawer can never show the previous selection's pair.
 *
 * Focus return is unchanged and still explicit: `Dialog` captures `document.activeElement` on
 * the way open — a matrix cell, a map terminal, a swimlane chip, or a reason-card button — and
 * restores it on close, because this app has no `DialogTrigger` for Radix to aim at.
 */
export function CaseDrawerHost({
  sources,
  versions,
}: {
  readonly sources: readonly SourceResource[]
  readonly versions: VersionStamp
}) {
  const drawer = useCaseDetailStore((state) => state.workspace.drawer)
  const closeDrawer = useCaseDetailStore((state) => state.closeDrawer)

  return (
    <>
      <SourceDrawer
        reference={drawer.kind === 'source' ? drawer.reference : null}
        sources={sources}
        versions={versions}
        onClose={closeDrawer}
      />
      <ComparisonDrawer
        candidate={drawer.kind === 'comparison' ? drawer.candidate : null}
        onClose={closeDrawer}
      />
    </>
  )
}

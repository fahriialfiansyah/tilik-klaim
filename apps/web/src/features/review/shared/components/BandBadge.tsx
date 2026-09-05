import { BAND_BASIS, BAND_LABELS } from '@/features/review/shared/labels'
import type { PriorityBand } from '@/features/review/shared/types'
import { cn } from '@/lib/utils'

/**
 * Priority band, always as colour **and** text.
 *
 * `design/DESIGN.md` forbids conveying status by colour alone, so the label is part of the
 * component rather than something each caller remembers to add. The `title` answers the
 * "kenapa pita ini?" hover the queue spec requires.
 */
const BAND_CLASSES: Record<PriorityBand, string> = {
  DETERMINISTIC_CONFLICT: 'bg-band-conflict-bg border-band-conflict-line text-band-conflict',
  HIGH_PRIORITY_SIGNAL: 'bg-band-signal-bg border-band-signal-line text-band-signal',
  NEEDS_CONTEXT: 'bg-band-context-bg border-band-context-line text-band-context',
  NO_OBSERVED_RISK: 'bg-band-quiet-bg border-band-quiet-line text-band-quiet',
}

/** The 3 px rail drawn down the left of a queue row. */
export const BAND_RAIL: Record<PriorityBand, string> = {
  DETERMINISTIC_CONFLICT: 'bg-band-conflict',
  HIGH_PRIORITY_SIGNAL: 'bg-band-signal',
  NEEDS_CONTEXT: 'bg-band-context',
  NO_OBSERVED_RISK: 'bg-band-quiet',
}

export function BandBadge({
  band,
  className,
}: {
  readonly band: PriorityBand
  readonly className?: string
}) {
  return (
    <span
      title={BAND_BASIS[band]}
      className={cn(
        'inline-block rounded-md border px-[10px] py-[3px] text-small font-semibold',
        BAND_CLASSES[band],
        className,
      )}
    >
      {BAND_LABELS[band]}
      {/*
        `title` reaches a mouse pointer and very little else — it is not focusable here and
        screen-reader support for it is inconsistent. The rationale is the part that keeps the
        band from reading as a verdict, so it is also rendered as text the reader announces
        rather than left to a hover the keyboard cannot reach.
      */}
      <span className="sr-only">: {BAND_BASIS[band]}</span>
    </span>
  )
}

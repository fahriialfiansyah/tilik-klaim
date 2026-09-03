import { useState } from 'react'

import { BriefingView } from '@/features/review/case-briefing/components/BriefingView'
import { useCaseBriefing } from '@/features/review/case-briefing/useCaseBriefing'
import type { EvidenceRef, SourceResource } from '@/features/review/case-detail/types'

/**
 * The briefing panel on `/cases/:id` — collapsed, below the evidence, on demand (ADR-0005).
 *
 * Its only coupling to the rest of the screen is `onOpenSource`, so a cited reference opens the
 * same drawer as every other reference. It has no path to the disposition draft.
 */
export function BriefingPanel({
  caseId,
  sources,
  onOpenSource,
}: {
  readonly caseId: string
  readonly sources: readonly SourceResource[]
  readonly onOpenSource: (reference: EvidenceRef) => void
}) {
  const [isOpen, setIsOpen] = useState(false)
  const { state, start } = useCaseBriefing(caseId)

  return (
    <BriefingView
      state={state}
      isOpen={isOpen}
      onToggle={() => setIsOpen((open) => !open)}
      onStart={start}
      sources={sources}
      onOpenSource={onOpenSource}
    />
  )
}

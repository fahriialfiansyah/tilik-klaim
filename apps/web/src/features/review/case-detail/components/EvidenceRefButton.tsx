import { AlertTriangle } from 'lucide-react'

import { AVAILABILITY_MEANINGS, RESOURCE_LABELS } from '@/features/review/case-detail/labels'
import type { EvidenceRef, SourceResource } from '@/features/review/case-detail/types'
import { cn } from '@/lib/utils'

/** Resolve a reference against the source index the detail response ships. */
export function findSource(
  sources: readonly SourceResource[],
  reference: EvidenceRef,
): SourceResource | null {
  return (
    sources.find(
      (source) =>
        source.resource_type === reference.resource_type &&
        source.resource_id === reference.resource_id,
    ) ?? null
  )
}

/**
 * One evidence reference, rendered as something that actually opens.
 *
 * Display rule 4 (`sprint/00-app-spec.md` § 4) is the whole reason this component exists: a
 * reference pointing at a resource the system cannot produce is an **evidence-integrity
 * defect**, not an empty panel and not a link that does nothing when clicked. So a reference
 * the index cannot resolve — or resolves as `MISSING` — is drawn as a flagged defect and is not
 * clickable, because there is nothing behind it to open and pretending otherwise is the failure
 * this rule names.
 *
 * The other three availabilities all open: `PRESENT` in full, `RELATED_BUNDLE` reduced to
 * non-identifying fields, `NOT_STORED` explaining that an episode or practitioner is referenced
 * by identity and never stored. None of those is a defect, and none is silent.
 */
export function EvidenceRefButton({
  reference,
  sources,
  onOpen,
}: {
  readonly reference: EvidenceRef
  readonly sources: readonly SourceResource[]
  readonly onOpen: (reference: EvidenceRef) => void
}) {
  const source = findSource(sources, reference)
  const isBroken = source === null || source.availability === 'MISSING'
  const name = `${RESOURCE_LABELS[reference.resource_type]} ${reference.resource_id}`

  if (isBroken) {
    return (
      <span
        data-testid="evidence-ref-broken"
        title={AVAILABILITY_MEANINGS.MISSING}
        className="inline-flex items-center gap-[6px] rounded-sm border border-band-conflict-line bg-band-conflict-bg px-2 py-[2px] text-meta text-band-conflict"
      >
        <AlertTriangle aria-hidden className="size-3" />
        {name}: cacat integritas bukti
        <span className="sr-only">. {AVAILABILITY_MEANINGS.MISSING}</span>
      </span>
    )
  }

  return (
    <button
      type="button"
      onClick={() => onOpen(reference)}
      className={cn(
        'rounded-sm text-start text-small text-brand underline underline-offset-2 hover:text-brand-hover',
      )}
    >
      {name}
      {source.availability === 'RELATED_BUNDLE' ? (
        <span className="text-ink-3"> · bundel pembanding</span>
      ) : null}
      {source.availability === 'NOT_STORED' ? (
        <span className="text-ink-3"> · dirujuk lewat identitas</span>
      ) : null}
    </button>
  )
}

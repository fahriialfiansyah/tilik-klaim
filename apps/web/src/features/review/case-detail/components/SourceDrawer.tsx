import { Dialog, DialogContent } from '@/components/ui/dialog'
import { PerfectScrollArea } from '@/components/wrappers/PerfectScrollArea'
import {
  AVAILABILITY_LABELS,
  AVAILABILITY_MEANINGS,
  RESOURCE_LABELS,
  sourceFieldLabel,
} from '@/features/review/case-detail/labels'
import { findSource } from '@/features/review/case-detail/components/EvidenceRefButton'
import { ExpandableText } from '@/features/review/shared/components/ExpandableText'
import type { EvidenceRef, SourceResource } from '@/features/review/case-detail/types'
import { formatIfTimestamp } from '@/features/review/shared/format'
import type { VersionStamp } from '@/modules/engine-version/useEngineVersion'
import { useLastPresent } from '@/lib/useLastPresent'
import { cn } from '@/lib/utils'

const AVAILABILITY_CLASSES: Record<SourceResource['availability'], string> = {
  PRESENT: 'border-line bg-sunk text-ink-2',
  RELATED_BUNDLE: 'border-band-context-line bg-band-context-bg text-band-context',
  NOT_STORED: 'border-band-quiet-line bg-band-quiet-bg text-band-quiet',
  MISSING: 'border-band-conflict-line bg-band-conflict-bg text-band-conflict',
}

/**
 * Widget 16 — the raw resource behind a reference, plus the engine versions in force.
 *
 * The panel always says which of the four availabilities applies before showing anything, so
 * a reduced view and a genuine defect can never be mistaken for one another. The versions are
 * here rather than only in the header because a reviewer reading a resource is deciding what a
 * *particular* ruleset made of it, and the audit event they are about to write cites both.
 */
export function SourceDrawer({
  reference,
  sources,
  versions,
  onClose,
}: {
  readonly reference: EvidenceRef | null
  readonly sources: readonly SourceResource[]
  readonly versions: VersionStamp
  readonly onClose: () => void
}) {
  // Kept for the closing frame so Radix can return focus to the reference that opened this.
  const shown = useLastPresent(reference)
  const source = shown ? findSource(sources, shown) : null

  return (
    <Dialog open={reference !== null} onOpenChange={(open) => !open && onClose()}>
      {shown ? (
        <DialogContent
          variant="drawer"
          title={`${RESOURCE_LABELS[shown.resource_type]} ${shown.resource_id}`}
          description="Isi sumber daya apa adanya, sebagaimana diterima sistem."
        >
          <PerfectScrollArea className="flex-1 px-5 py-4">
            <p
              className={cn(
                'mb-4 inline-block rounded-md border px-[10px] py-[3px] text-small font-semibold',
                AVAILABILITY_CLASSES[source?.availability ?? 'MISSING'],
              )}
            >
              {AVAILABILITY_LABELS[source?.availability ?? 'MISSING']}
            </p>
            <p className="mb-5 text-small leading-relaxed text-ink-2 text-pretty">
              {AVAILABILITY_MEANINGS[source?.availability ?? 'MISSING']}
            </p>

            {source && source.fields.length > 0 ? (
              <dl className="mb-6">
                {source.fields.map((field) => (
                  <div
                    key={field.name}
                    className="flex gap-4 border-t border-line py-[9px] text-small"
                  >
                    <dt className="w-[168px] shrink-0 text-ink-3">
                      {sourceFieldLabel(field.name)}
                    </dt>
                    <dd data-numeric className="min-w-0 flex-1">
                      <ExpandableText text={formatIfTimestamp(field.value)} />
                    </dd>
                  </div>
                ))}
              </dl>
            ) : null}

            <p className="font-mono text-micro font-semibold tracking-label text-ink-3">
              VERSI MESIN SAAT KASUS DISARING
            </p>
            <p data-numeric className="mt-[6px] font-mono text-meta text-ink-2">
              skema v{versions.schema_version} · aturan v{versions.ruleset_version} · mesin v
              {versions.engine_version}
            </p>
          </PerfectScrollArea>
        </DialogContent>
      ) : null}
    </Dialog>
  )
}

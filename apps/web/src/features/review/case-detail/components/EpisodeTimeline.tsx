import { EvidenceRefButton } from '@/features/review/case-detail/components/EvidenceRefButton'
import type {
  EvidenceRef,
  SourceResource,
  TimelineEvent,
} from '@/features/review/case-detail/types'
import { formatDateTime } from '@/features/review/shared/format'
import { cn } from '@/lib/utils'

/** Timeline dots carry the kind as colour *and* as the visible `kind` word beside them. */
const KIND_DOT: Record<string, string> = {
  encounter: 'border-brand',
  procedure: 'border-band-context',
  medication: 'border-line-strong',
}

const KIND_LABELS: Record<string, string> = {
  encounter: 'Kunjungan',
  procedure: 'Tindakan',
  medication: 'Obat',
}

/**
 * Widget 14 — the episode in time order.
 *
 * The sequence is what turns "a line has no procedure record" into something a person can
 * judge: whether the visit happened at all, whether anything was done during it, and where the
 * billed service should have appeared. Each entry's resource opens, like every other reference
 * on this screen.
 */
export function EpisodeTimeline({
  events,
  sources,
  onOpenSource,
}: {
  readonly events: readonly TimelineEvent[]
  readonly sources: readonly SourceResource[]
  readonly onOpenSource: (reference: EvidenceRef) => void
}) {
  return (
    <section
      aria-label="Linimasa episode"
      className="rounded-lg border border-line bg-card p-[18px] shadow-panel"
    >
      <p className="mb-[14px] text-small font-semibold">Linimasa episode</p>

      {events.length === 0 ? (
        <p className="text-small text-ink-3">
          Bundel ini tidak memuat kejadian yang dapat diurutkan dalam waktu.
        </p>
      ) : (
        <ol>
          {events.map((event, index) => (
            <li key={`${event.occurred_at}-${event.label}`} className="flex gap-[14px] pb-4">
              <span
                data-numeric
                className="w-[110px] shrink-0 pt-[2px] font-mono text-meta text-ink-3"
              >
                {formatDateTime(event.occurred_at)}
              </span>
              <span aria-hidden className="flex shrink-0 flex-col items-center gap-1">
                <span
                  className={cn(
                    'mt-[5px] size-[10px] rounded-full border-2 bg-card',
                    KIND_DOT[event.kind] ?? 'border-line-strong',
                  )}
                />
                {index < events.length - 1 ? <span className="w-px flex-1 bg-line" /> : null}
              </span>
              <span className="min-w-0 flex-1">
                <span className="block text-small leading-snug">{event.label}</span>
                <span className="mt-[3px] flex flex-wrap items-center gap-x-3 text-meta text-ink-3">
                  {KIND_LABELS[event.kind] ?? event.kind}
                  {event.resource ? (
                    <EvidenceRefButton
                      reference={event.resource}
                      sources={sources}
                      onOpen={onOpenSource}
                    />
                  ) : null}
                </span>
              </span>
            </li>
          ))}
        </ol>
      )}
    </section>
  )
}

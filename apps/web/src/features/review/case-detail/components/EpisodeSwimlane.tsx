import { PerfectScrollArea } from '@/components/wrappers/PerfectScrollArea'
import { EvidenceRefButton } from '@/features/review/case-detail/components/EvidenceRefButton'
import { laneLabel } from '@/features/review/case-detail/labels'
import { swimlanes, type LaneEvent, type Swimlane } from '@/features/review/case-detail/swimlanes'
import type { CaseDetail, EvidenceRef } from '@/features/review/case-detail/types'
import { formatDate, formatTime } from '@/features/review/shared/format'
import { cn } from '@/lib/utils'

const MICRO_LABEL = 'font-mono text-micro font-semibold tracking-label text-ink-3'

/** Lane accents. The billing lane is brand-coloured because it is what the case is *about*. */
const LANE_RAIL: Record<string, string> = {
  encounter: 'bg-line-strong',
  procedure: 'bg-band-context',
  medication: 'bg-line-strong',
  billing: 'bg-brand',
}

function EventChip({
  event,
  sources,
  onOpenSource,
}: {
  readonly event: LaneEvent
  readonly sources: CaseDetail['sources']
  readonly onOpenSource: (reference: EvidenceRef) => void
}) {
  return (
    <span className="block rounded-md border border-line bg-sunk px-[9px] py-[6px] text-meta">
      <span className="block leading-snug">{event.label}</span>
      {event.resource ? (
        <EvidenceRefButton reference={event.resource} sources={sources} onOpen={onOpenSource} />
      ) : null}
    </span>
  )
}

function LaneRow({
  lane,
  ticks,
  sources,
  onOpenSource,
}: {
  readonly lane: Swimlane
  readonly ticks: readonly string[]
  readonly sources: CaseDetail['sources']
  readonly onOpenSource: (reference: EvidenceRef) => void
}) {
  const isEmpty = lane.events.length === 0
  return (
    <tr className="border-t border-line">
      <th scope="row" className="min-w-[112px] px-3 py-[9px] text-left align-top font-normal">
        <span className="flex items-start gap-2">
          <span aria-hidden className={cn('mt-[5px] h-[10px] w-[3px] shrink-0 rounded-sm', LANE_RAIL[lane.kind] ?? 'bg-line-strong')} />
          <span>
            <span className="block text-small font-medium">{laneLabel(lane.kind)}</span>
            {/* Drawn and said in words: an empty lane is the finding, not a rendering gap. */}
            {isEmpty ? (
              <span className="block text-meta text-ink-3">tidak ada kejadian tercatat</span>
            ) : null}
          </span>
        </span>
      </th>
      {ticks.map((tick) => {
        const here = lane.events.filter((event) => event.tick === tick)
        return (
          <td key={tick} className="min-w-[104px] px-2 py-[9px] align-top">
            {here.length > 0 ? (
              <span className="flex flex-col gap-1">
                {here.map((event) => (
                  <EventChip key={event.key} event={event} sources={sources} onOpenSource={onOpenSource} />
                ))}
              </span>
            ) : null}
          </td>
        )
      })}
    </tr>
  )
}

/**
 * Widget 14 — the episode as swimlanes (ADR-0004).
 *
 * One table: lanes are rows, distinct minutes are columns. A billed service in the *Penagihan*
 * lane with an empty *Tindakan* lane above it is the phantom finding drawn rather than
 * narrated. Each lane keeps its own accessible row, every resource still opens, and the axis is
 * the same for all four lanes so two events in the same minute sit in the same column.
 */
export function EpisodeSwimlane({
  detail,
  onOpenSource,
}: {
  readonly detail: CaseDetail
  readonly onOpenSource: (reference: EvidenceRef) => void
}) {
  const model = swimlanes(detail)
  const dates = [...new Set(model.ticks.map((tick) => formatDate(tick)))]
  const showDate = dates.length > 1

  return (
    <section
      aria-label="Linimasa episode"
      className="overflow-hidden rounded-lg border border-line bg-card shadow-panel"
    >
      <div className="border-b border-line px-[15px] py-[13px]">
        <p className="text-small font-semibold">Linimasa episode</p>
        <p className="mt-[2px] text-meta text-ink-3">
          Empat jalur pada satu sumbu waktu{showDate ? '' : ` · ${dates[0] ?? ''}`}. Jalur kosong
          tetap digambar.
        </p>
      </div>

      {model.ticks.length === 0 ? (
        <p className="px-[15px] py-6 text-small text-ink-3">
          Bundel ini tidak memuat kejadian yang dapat diurutkan dalam waktu.
        </p>
      ) : (
        <PerfectScrollArea axis="both" className="max-w-full">
          <table aria-label="Linimasa episode" className="w-full border-collapse text-small">
            <thead>
              <tr className="bg-sunk">
                <th scope="col" className={cn('px-3 py-2 text-left', MICRO_LABEL)}>
                  JALUR
                </th>
                {model.ticks.map((tick) => (
                  <th key={tick} scope="col" data-numeric className={cn('px-2 py-2 text-left font-mono', MICRO_LABEL)}>
                    {showDate ? `${formatDate(tick)} ` : ''}
                    {formatTime(tick)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {model.lanes.map((lane) => (
                <LaneRow
                  key={lane.kind}
                  lane={lane}
                  ticks={model.ticks}
                  sources={detail.sources}
                  onOpenSource={onOpenSource}
                />
              ))}
            </tbody>
          </table>
        </PerfectScrollArea>
      )}
    </section>
  )
}

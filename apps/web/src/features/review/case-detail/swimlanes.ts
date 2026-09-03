import { findSource } from '@/features/review/case-detail/components/EvidenceRefButton'
import type { CaseDetail, EvidenceRef, TimelineEvent } from '@/features/review/case-detail/types'

/**
 * The Episode Timeline as swimlanes — widget 14, re-shaped per ADR-0004.
 *
 * Four lanes over one shared axis. Three come from the timeline the API already sends; the
 * fourth, *Penagihan*, is derived here from `lines[].service_at`, which is also already on the
 * wire. Nothing was added to the payload for this, deliberately: a lane sourced from the backend
 * would rewrite a committed contract fixture for a presentational gain.
 *
 * A lane is always present, populated or not. The phantom finding *is* an empty procedure lane
 * beside a populated billing lane, and a lane that collapsed when empty would hide exactly the
 * absence the reviewer is here to judge.
 */
export const LANE_ORDER = ['encounter', 'procedure', 'medication', 'billing'] as const
export type KnownLaneKind = (typeof LANE_ORDER)[number]

export type LaneEvent = {
  readonly key: string
  readonly occurred_at: string
  /** The minute this event sits on, shared with every other lane. */
  readonly tick: string
  readonly label: string
  readonly resource: EvidenceRef | null
}

export type Swimlane = {
  readonly kind: KnownLaneKind | string
  readonly events: readonly LaneEvent[]
}

export type SwimlaneModel = {
  readonly lanes: readonly Swimlane[]
  /** Distinct minutes across all lanes, ascending. The columns of the shared axis. */
  readonly ticks: readonly string[]
}

const MS_PER_MINUTE = 60_000

/** Two events in the same minute share a column; sub-minute jitter is not a sequence. */
function tickOf(isoTimestamp: string): string {
  const value = new Date(isoTimestamp).getTime()
  if (Number.isNaN(value)) {
    return isoTimestamp
  }
  return new Date(Math.floor(value / MS_PER_MINUTE) * MS_PER_MINUTE).toISOString()
}

function byTime(left: LaneEvent, right: LaneEvent): number {
  return left.occurred_at.localeCompare(right.occurred_at)
}

function fromTimeline(event: TimelineEvent, index: number): LaneEvent {
  return {
    key: `${event.kind}:${event.resource?.resource_id ?? index}`,
    occurred_at: event.occurred_at,
    tick: tickOf(event.occurred_at),
    label: event.label,
    resource: event.resource,
  }
}

/**
 * A billed line opens as a reference only when the source index can produce it — which is when
 * a reason cited it. A line nobody cited is not in the index, and drawing it as a reference
 * would make display rule 4 flag a defect on a line that is simply not part of any finding.
 * It is named in the label instead, so nothing is hidden and nothing is accused.
 */
function billingEvents(detail: CaseDetail): readonly LaneEvent[] {
  return detail.lines.map((line) => {
    const reference: EvidenceRef = {
      resource_type: 'ClaimLine',
      resource_id: line.line_id,
      label: line.line_id,
    }
    const isIndexed = findSource(detail.sources, reference) !== null
    return {
      key: `billing:${line.line_id}`,
      occurred_at: line.service_at,
      tick: tickOf(line.service_at),
      label: isIndexed ? line.description : `${line.description} · ${line.line_id}`,
      resource: isIndexed ? reference : null,
    }
  })
}

export function swimlanes(detail: CaseDetail): SwimlaneModel {
  const grouped = new Map<string, LaneEvent[]>()
  for (const kind of LANE_ORDER) {
    grouped.set(kind, [])
  }
  detail.timeline.forEach((event, index) => {
    const lane = grouped.get(event.kind) ?? []
    grouped.set(event.kind, [...lane, fromTimeline(event, index)])
  })
  grouped.set('billing', [...billingEvents(detail)])

  const lanes = [...grouped.entries()].map(([kind, events]) => ({
    kind,
    events: [...events].sort(byTime),
  }))
  const ticks = [...new Set(lanes.flatMap((lane) => lane.events.map((event) => event.tick)))].sort()
  return { lanes, ticks }
}

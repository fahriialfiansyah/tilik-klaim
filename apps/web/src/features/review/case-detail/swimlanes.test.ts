import { describe, expect, test } from 'vitest'

import { LANE_ORDER, swimlanes } from '@/features/review/case-detail/swimlanes'
import { makeCaseDetail } from '@/features/review/case-detail/test-fixtures'

describe('lanes', () => {
  test('the four lanes appear in a fixed order, populated or not', () => {
    const { lanes } = swimlanes(makeCaseDetail())
    expect(lanes.map((lane) => lane.kind)).toEqual([...LANE_ORDER])
  })

  /**
   * The phantom picture: the billed service sits in the *Penagihan* lane and the *Tindakan*
   * lane beside it is empty. An empty lane must exist to be seen — a lane that collapses when
   * it has nothing in it hides exactly the absence the reviewer is here to judge.
   */
  test('the procedure lane is present and empty on the phantom fixture', () => {
    const { lanes } = swimlanes(makeCaseDetail())
    const procedures = lanes.find((lane) => lane.kind === 'procedure')
    expect(procedures?.events).toEqual([])
  })

  test('the billing lane is derived from the billed lines, one event per line', () => {
    const { lanes } = swimlanes(makeCaseDetail())
    const billing = lanes.find((lane) => lane.kind === 'billing')
    expect(billing?.events.map((event) => event.key)).toEqual(['billing:LN-P1', 'billing:LN-P2'])
    expect(billing?.events[0].occurred_at).toBe('2026-07-01T09:00:00Z')
  })

  test('events stay in time order within a lane', () => {
    const detail = makeCaseDetail({
      timeline: [
        { occurred_at: '2026-07-01T10:00:00Z', kind: 'procedure', label: 'later', resource: null },
        { occurred_at: '2026-07-01T08:30:00Z', kind: 'procedure', label: 'earlier', resource: null },
      ],
    })
    const lane = swimlanes(detail).lanes.find((entry) => entry.kind === 'procedure')
    expect(lane?.events.map((event) => event.label)).toEqual(['earlier', 'later'])
  })

  test('a kind the client does not know is appended as its own lane rather than dropped', () => {
    const detail = makeCaseDetail({
      timeline: [{ occurred_at: '2026-07-01T08:00:00Z', kind: 'document', label: 'note', resource: null }],
    })
    const kinds = swimlanes(detail).lanes.map((lane) => lane.kind)
    expect(kinds).toEqual([...LANE_ORDER, 'document'])
  })
})

describe('the shared axis', () => {
  test('ticks are the distinct minutes across every lane, sorted', () => {
    const { ticks } = swimlanes(makeCaseDetail())
    expect(ticks).toEqual(['2026-07-01T08:00:00.000Z', '2026-07-01T09:00:00.000Z', '2026-07-01T10:00:00.000Z'])
  })

  test('every event carries the tick it sits on', () => {
    const { lanes, ticks } = swimlanes(makeCaseDetail())
    for (const lane of lanes) {
      for (const event of lane.events) {
        expect(ticks).toContain(event.tick)
      }
    }
  })

  test('an empty bundle has no ticks and four empty lanes', () => {
    const model = swimlanes(makeCaseDetail({ timeline: [], lines: [] }))
    expect(model.ticks).toEqual([])
    expect(model.lanes.every((lane) => lane.events.length === 0)).toBe(true)
  })
})

describe('billed lines the reasons never cited', () => {
  /**
   * Found by looking at the rendered page, not by any test: the billing lane flagged line
   * 89.7 as "cacat integritas bukti" in red. The API indexes sources for the resources the
   * *reasons* cite plus the timeline's own references; a billed line nobody cited is in
   * neither, so drawing it as an evidence reference makes display rule 4 fire on a line that
   * is simply not part of any finding. It carries no reference — the label names it instead.
   */
  test('carry no reference when the source index does not hold the line', () => {
    const { lanes } = swimlanes(makeCaseDetail())
    const billing = lanes.find((lane) => lane.kind === 'billing')
    const uncited = billing?.events.find((event) => event.label.includes('89.7'))
    expect(uncited?.resource).toBeNull()
    expect(uncited?.label).toContain('LN-P1')
  })

  test('carry a reference when a reason cited the line and the index resolves it', () => {
    const { lanes } = swimlanes(makeCaseDetail())
    const billing = lanes.find((lane) => lane.kind === 'billing')
    const cited = billing?.events.find((event) => event.label.includes('88.71'))
    expect(cited?.resource?.resource_id).toBe('LN-P2')
  })
})

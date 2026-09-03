import { cellFor, resolvedState, type MatrixCellState } from '@/features/review/case-detail/matrix'
import type {
  CaseDetail,
  CounterEvidenceNote,
  EvidenceRef,
  Reason,
  ResourceType,
} from '@/features/review/case-detail/types'

/**
 * The Evidence Map — widget 15, re-shaped per ADR-0004.
 *
 * Anchored on the **open reason** rather than the selected line: the question a reviewer holds
 * is "what does this reason claim, and what backs or weakens it", and the line follows.
 *
 * **Display rule 3 — one path, not a network — is kept structurally.** The model is a trunk
 * (claim → cited line) with terminals hanging off its last node. Terminals have no successors
 * and never reference each other, so every node has exactly one path from the root. If a
 * future change gives a node two parents, `assertSinglePath` fails in development and the
 * change is wrong — the rule says so in as many words.
 */
export type MapNodeState = Exclude<MatrixCellState, 'NOT_EXPECTED'>

export type MapNode = {
  readonly key: string
  readonly type: ResourceType | 'Claim'
  readonly label: string
  readonly reference: EvidenceRef | null
  readonly state: MapNodeState
}

export type EvidenceMapModel = {
  readonly trunk: readonly MapNode[]
  readonly terminals: readonly MapNode[]
  readonly counter: readonly CounterEvidenceNote[]
}

const NOT_ON_A_TERMINAL: ReadonlySet<ResourceType> = new Set(['ClaimLine'])

function citedLines(reason: Reason): readonly EvidenceRef[] {
  return reason.evidence.filter((ref) => ref.resource_type === 'ClaimLine')
}

/** The line node follows the selection when the reason cites it; otherwise the first cited. */
function lineNode(detail: CaseDetail, reason: Reason, selectedLineId: string | null): MapNode {
  const cited = citedLines(reason)
  const chosen = cited.find((ref) => ref.resource_id === selectedLineId) ?? cited[0] ?? null
  const line = chosen ? detail.lines.find((entry) => entry.line_id === chosen.resource_id) : null
  return {
    key: 'line',
    type: 'ClaimLine',
    label: chosen ? (line?.description ?? chosen.resource_id) : 'tidak ada baris tertentu dirujuk',
    reference: chosen,
    state: chosen ? resolvedState([chosen], detail.sources) : 'FOUND',
  }
}

function terminalsFor(detail: CaseDetail, reason: Reason): readonly MapNode[] {
  const types = new Set<ResourceType>([
    ...reason.expected_support,
    ...reason.evidence.map((ref) => ref.resource_type),
  ])
  const nodes: MapNode[] = []
  for (const type of [...types].filter((entry) => !NOT_ON_A_TERMINAL.has(entry)).sort()) {
    const cell = cellFor([reason], type, detail.sources)
    if (cell.refs.length === 0) {
      nodes.push({ key: `expected:${type}`, type, label: 'tidak ditemukan', reference: null, state: 'MISSING' })
      continue
    }
    // One terminal per reference: two cited notes are two leaves, never one node shared by
    // two parents — that is the shape display rule 3 forbids.
    for (const ref of cell.refs) {
      nodes.push({
        key: `ref:${type}:${ref.resource_id}`,
        type,
        label: ref.resource_id,
        reference: ref,
        state: resolvedState([ref], detail.sources),
      })
    }
  }
  return nodes
}

export function mapForReason(
  detail: CaseDetail,
  reason: Reason,
  selectedLineId: string | null,
): EvidenceMapModel {
  const claim: MapNode = {
    key: 'claim',
    type: 'Claim',
    label: detail.case_id.replace(/^case_/, '').slice(0, 10),
    reference: null,
    state: 'FOUND',
  }
  return {
    trunk: [claim, lineNode(detail, reason, selectedLineId)],
    terminals: terminalsFor(detail, reason),
    counter: reason.counter_evidence_notes,
  }
}

/**
 * The structural form of "no node has two parents": every key appears once. A duplicate key
 * would mean one resource drawn under two paths — the moment a path becomes a web.
 */
export function assertSinglePath(model: EvidenceMapModel): void {
  const keys = [...model.trunk, ...model.terminals].map((node) => node.key)
  const duplicates = keys.filter((key, index) => keys.indexOf(key) !== index)
  if (duplicates.length > 0) {
    throw new Error(`Evidence map is no longer a single path; duplicated: ${duplicates.join(', ')}`)
  }
}

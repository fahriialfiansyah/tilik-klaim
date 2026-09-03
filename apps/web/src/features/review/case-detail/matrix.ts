import { findSource } from '@/features/review/case-detail/components/EvidenceRefButton'
import type {
  CaseDetail,
  ClaimLineView,
  EvidenceRef,
  Reason,
  ResourceType,
  SourceResource,
} from '@/features/review/case-detail/types'
import { RESOURCE_TYPES } from '@/features/review/case-detail/types'

/**
 * The Evidence Matrix — widget 28, ADR-0004.
 *
 * Rows are billed lines, columns are the resource types the reasons expected or cited, and each
 * cell says what stands between them. Everything here is derived from the `GET /v1/cases/{id}`
 * response as it already ships; no field was added for it.
 *
 * **Four states, not two.** `NOT_EXPECTED` is the one that matters: a cell no reason ever
 * looked at must read as "nobody expected this here", never as "this is absent". Collapsing it
 * into `MISSING` would manufacture a finding the data does not make — the same failure
 * `07_privacy_threat_model.md` names as "Incomplete RME looks like phantom billing".
 * `UNRESOLVED` is display rule 4's defect: a reference that points at nothing.
 */
export const MATRIX_CELL_STATES = ['FOUND', 'MISSING', 'UNRESOLVED', 'NOT_EXPECTED'] as const
export type MatrixCellState = (typeof MATRIX_CELL_STATES)[number]

export type MatrixCell = {
  readonly type: ResourceType
  readonly state: MatrixCellState
  readonly refs: readonly EvidenceRef[]
}

export type MatrixRow = {
  /** The line id, or `claim` for reasons that cite no particular line. */
  readonly key: string
  readonly line: ClaimLineView | null
  readonly reasonCodes: readonly string[]
  readonly cells: readonly MatrixCell[]
}

export type EvidenceMatrix = {
  readonly columns: readonly ResourceType[]
  readonly rows: readonly MatrixRow[]
}

export const CLAIM_ROW_KEY = 'claim'

/** The row *is* the line; a ClaimLine column would only ever point at itself. */
const NEVER_A_COLUMN: ReadonlySet<ResourceType> = new Set(['ClaimLine'])

function citesLine(reason: Reason, lineId: string): boolean {
  return reason.evidence.some(
    (ref) => ref.resource_type === 'ClaimLine' && ref.resource_id === lineId,
  )
}

function citesAnyLine(reason: Reason): boolean {
  return reason.evidence.some((ref) => ref.resource_type === 'ClaimLine')
}

function dedupe(refs: readonly EvidenceRef[]): readonly EvidenceRef[] {
  const seen = new Set<string>()
  return refs.filter((ref) => {
    const key = `${ref.resource_type}:${ref.resource_id}`
    if (seen.has(key)) {
      return false
    }
    seen.add(key)
    return true
  })
}

/** Found, unless any of the references points at something the index cannot produce. */
export function resolvedState(
  refs: readonly EvidenceRef[],
  sources: readonly SourceResource[],
): Extract<MatrixCellState, 'FOUND' | 'UNRESOLVED'> {
  const broken = refs.some((ref) => {
    const source = findSource(sources, ref)
    return source === null || source.availability === 'MISSING'
  })
  return broken ? 'UNRESOLVED' : 'FOUND'
}

/** What a set of reasons says about one resource type. Shared with the Evidence Map. */
export function cellFor(
  reasons: readonly Reason[],
  type: ResourceType,
  sources: readonly SourceResource[],
): MatrixCell {
  const isExpected = reasons.some((reason) => reason.expected_support.includes(type))
  const refs = dedupe(
    reasons.flatMap((reason) => reason.evidence.filter((ref) => ref.resource_type === type)),
  )
  if (!isExpected && refs.length === 0) {
    return { type, state: 'NOT_EXPECTED', refs }
  }
  if (refs.length === 0) {
    return { type, state: 'MISSING', refs }
  }
  return { type, state: resolvedState(refs, sources), refs }
}

function columnsFor(reasons: readonly Reason[]): readonly ResourceType[] {
  const wanted = new Set<ResourceType>()
  for (const reason of reasons) {
    reason.expected_support.forEach((type) => wanted.add(type))
    reason.evidence.forEach((ref) => wanted.add(ref.resource_type))
  }
  // Catalog order, so two cases with the same types show them in the same place.
  return RESOURCE_TYPES.filter((type) => wanted.has(type) && !NEVER_A_COLUMN.has(type))
}

function row(
  key: string,
  line: ClaimLineView | null,
  reasons: readonly Reason[],
  columns: readonly ResourceType[],
  sources: readonly SourceResource[],
): MatrixRow {
  return {
    key,
    line,
    reasonCodes: reasons.map((reason) => reason.code),
    cells: columns.map((type) => cellFor(reasons, type, sources)),
  }
}

export function buildEvidenceMatrix(detail: CaseDetail): EvidenceMatrix {
  const columns = columnsFor(detail.reasons)
  const lineRows = detail.lines.map((line) =>
    row(
      line.line_id,
      line,
      detail.reasons.filter((reason) => citesLine(reason, line.line_id)),
      columns,
      detail.sources,
    ),
  )
  // Repeat, clone and unbundling cite the claim, a visit or a note rather than a line. They
  // need a row of their own or the matrix under-reports how many reasons the case has.
  const claimLevel = detail.reasons.filter((reason) => !citesAnyLine(reason))
  const rows =
    claimLevel.length > 0
      ? [...lineRows, row(CLAIM_ROW_KEY, null, claimLevel, columns, detail.sources)]
      : lineRows
  return { columns, rows }
}

/** Types with at least one MISSING cell — what the matrix says the record lacks. */
export function matrixMissingTypes(matrix: EvidenceMatrix): readonly ResourceType[] {
  const missing = new Set<ResourceType>()
  for (const entry of matrix.rows) {
    for (const cell of entry.cells) {
      if (cell.state === 'MISSING') {
        missing.add(cell.type)
      }
    }
  }
  return matrix.columns.filter((type) => missing.has(type))
}

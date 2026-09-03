import { describe, expect, test } from 'vitest'

import { buildEvidenceMatrix, matrixMissingTypes } from '@/features/review/case-detail/matrix'
import { missingEvidenceTypes } from '@/features/review/case-detail/selectors'
import {
  PHANTOM_REASON,
  REPEAT_REASON,
  SOURCES,
  makeCaseDetail,
} from '@/features/review/case-detail/test-fixtures'

function cell(detail = makeCaseDetail(), rowKey = 'LN-P2', type = 'Procedure') {
  const matrix = buildEvidenceMatrix(detail)
  const row = matrix.rows.find((entry) => entry.key === rowKey)
  const found = row?.cells.find((entry) => entry.type === type)
  if (!found) {
    throw new Error(`no cell ${rowKey}/${type}`)
  }
  return found
}

describe('the four cell states', () => {
  test('a line expecting a Procedure with none cited is MISSING — the phantom finding', () => {
    expect(cell().state).toBe('MISSING')
  })

  test('an expected type the reason cites and the index resolves is FOUND', () => {
    const found = cell(makeCaseDetail(), 'LN-P2', 'Encounter')
    expect(found.state).toBe('FOUND')
    expect(found.refs.map((ref) => ref.resource_id)).toEqual(['ENC-PH-1'])
  })

  /**
   * ADR-0004: a reference exists but points at nothing. That is display rule 4's defect and
   * must not be drawn as "missing" — missing means the record never cited it; unresolved means
   * it cited something the system cannot produce. Different finding, different next action.
   */
  test('a cited reference whose source is MISSING is UNRESOLVED, not MISSING', () => {
    const detail = makeCaseDetail({
      sources: SOURCES.map((source) =>
        source.resource_id === 'ENC-PH-1' ? { ...source, availability: 'MISSING' as const } : source,
      ),
    })
    expect(cell(detail, 'LN-P2', 'Encounter').state).toBe('UNRESOLVED')
  })

  test('a cited reference absent from the index altogether is also UNRESOLVED', () => {
    expect(cell(makeCaseDetail({ sources: [] }), 'LN-P2', 'Encounter').state).toBe('UNRESOLVED')
  })

  /**
   * The fourth state is the one that matters. LN-P1 is cited by no reason, so its Procedure
   * cell must read "nobody expected this here", never "this is absent" — the difference between
   * an empty cell and a manufactured finding.
   */
  test('a type no citing reason expects is NOT_EXPECTED, on a line no reason cites', () => {
    expect(cell(makeCaseDetail(), 'LN-P1', 'Procedure').state).toBe('NOT_EXPECTED')
    expect(cell(makeCaseDetail(), 'LN-P1', 'Encounter').state).toBe('NOT_EXPECTED')
  })
})

describe('shape', () => {
  test('rows follow the billed lines in order', () => {
    const { rows } = buildEvidenceMatrix(makeCaseDetail())
    expect(rows.map((row) => row.key)).toEqual(['LN-P1', 'LN-P2'])
  })

  test('columns are the union of expected and cited types, never ClaimLine, in catalog order', () => {
    const { columns } = buildEvidenceMatrix(makeCaseDetail())
    expect(columns).toEqual(['Encounter', 'Procedure'])
  })

  test('a row names the reasons that cite it', () => {
    const { rows } = buildEvidenceMatrix(makeCaseDetail())
    expect(rows[1].reasonCodes).toEqual(['LINE_WITHOUT_COMPLETED_PROCEDURE'])
    expect(rows[0].reasonCodes).toEqual([])
  })

  /**
   * Repeat, clone and unbundling reasons cite the claim, an encounter, or a document — not a
   * line. Without a row of their own they would vanish from the matrix, and a matrix that only
   * shows line-level findings would tell a reviewer the case has fewer reasons than it does.
   */
  test('a reason citing no line gets a claim-level row', () => {
    const detail = makeCaseDetail({ reasons: [PHANTOM_REASON, REPEAT_REASON] })
    const { rows, columns } = buildEvidenceMatrix(detail)
    const claimRow = rows.find((row) => row.key === 'claim')
    expect(claimRow?.line).toBeNull()
    expect(claimRow?.reasonCodes).toEqual(['DUPLICATE_CLAIM_FINGERPRINT'])
    expect(columns).toContain('Claim')
    expect(claimRow?.cells.find((entry) => entry.type === 'Claim')?.state).toBe('FOUND')
  })

  test('no claim-level row appears when every reason cites a line', () => {
    expect(buildEvidenceMatrix(makeCaseDetail()).rows.some((row) => row.key === 'claim')).toBe(false)
  })

  test('a case with no reasons has rows but no columns', () => {
    const quiet = buildEvidenceMatrix(makeCaseDetail({ reasons: [], primary_reason: null }))
    expect(quiet.columns).toEqual([])
    expect(quiet.rows).toHaveLength(2)
  })
})

describe('agreement with the request-evidence checklist', () => {
  /**
   * `missingEvidenceTypes()` pre-ticks the checklist. Both read `expected_support` against
   * `evidence`, so every type the checklist asks for must show as MISSING somewhere in the
   * matrix — otherwise the panel would ask for a document the matrix says was found.
   */
  test('every type the checklist asks for is MISSING in at least one cell', () => {
    const detail = makeCaseDetail()
    const asked = missingEvidenceTypes(detail)
    const shown = matrixMissingTypes(buildEvidenceMatrix(detail))
    expect(asked.every((type) => shown.includes(type))).toBe(true)
    expect(shown).toEqual(['Procedure'])
  })
})

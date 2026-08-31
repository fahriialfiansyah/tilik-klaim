import { describe, expect, test } from 'vitest'

import {
  comparisonForReason,
  missingEvidenceTypes,
  primaryLineId,
  requestableEvidenceTypes,
} from '@/features/review/case-detail/selectors'
import {
  CLONE_COMPARISON,
  PHANTOM_REASON,
  makeCaseDetail,
} from '@/features/review/case-detail/test-fixtures'

describe('missingEvidenceTypes', () => {
  test('names the expected type the reasons did not find', () => {
    expect(missingEvidenceTypes(makeCaseDetail())).toEqual(['Procedure'])
  })

  test('excludes a type that was found, even on a different reason', () => {
    expect(missingEvidenceTypes(makeCaseDetail())).not.toContain('Encounter')
  })

  test('a case with no reasons is missing nothing', () => {
    const quiet = makeCaseDetail({ reasons: [], primary_reason: null })
    expect(missingEvidenceTypes(quiet)).toEqual([])
  })
})

describe('requestableEvidenceTypes', () => {
  test('offers the missing types first, so the pre-checked ones read together', () => {
    expect(requestableEvidenceTypes(makeCaseDetail())[0]).toBe('Procedure')
  })

  test('falls back to a general list when no reason expects anything', () => {
    const quiet = makeCaseDetail({ reasons: [], primary_reason: null })
    expect(requestableEvidenceTypes(quiet).length).toBeGreaterThan(0)
  })
})

describe('primaryLineId', () => {
  test('selects the line the strongest reason cites', () => {
    expect(primaryLineId(makeCaseDetail())).toBe('LN-P2')
  })

  test('falls back to the first line that is not fully supported', () => {
    const noCitation = makeCaseDetail({
      reasons: [{ ...PHANTOM_REASON, evidence: [] }],
    })
    expect(primaryLineId(noCitation)).toBe('LN-P2')
  })

  test('returns null when the bundle carried no billed lines', () => {
    expect(primaryLineId(makeCaseDetail({ lines: [] }))).toBeNull()
  })
})

describe('comparisonForReason', () => {
  /**
   * A "Bandingkan" button that opened the wrong pair would be worse than no button: the
   * reviewer would be comparing this case against a candidate belonging to a different reason.
   */
  test('a reason whose mode has no comparison offers none', () => {
    expect(comparisonForReason(makeCaseDetail(), 0)).toBeNull()
  })

  test('a clone reason is paired with its own candidate', () => {
    const clone = makeCaseDetail({
      reasons: [{ ...PHANTOM_REASON, mode: 'CLONED_DOCUMENTATION' }],
      comparisons: [CLONE_COMPARISON],
    })
    expect(comparisonForReason(clone, 0)).toBe(CLONE_COMPARISON)
  })

  test('a non-comparison reason listed first does not shift the pairing', () => {
    const mixed = makeCaseDetail({
      reasons: [PHANTOM_REASON, { ...PHANTOM_REASON, mode: 'CLONED_DOCUMENTATION' }],
      comparisons: [CLONE_COMPARISON],
    })
    expect(comparisonForReason(mixed, 0)).toBeNull()
    expect(comparisonForReason(mixed, 1)).toBe(CLONE_COMPARISON)
  })
})

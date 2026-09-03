import { describe, expect, test } from 'vitest'

import { assertSinglePath, mapForReason } from '@/features/review/case-detail/map'
import {
  PHANTOM_REASON,
  REPEAT_REASON,
  SOURCES,
  makeCaseDetail,
} from '@/features/review/case-detail/test-fixtures'

describe('display rule 3 — one trunk, terminals that fan out and never interconnect', () => {
  test('the trunk is claim then the cited line, in that order', () => {
    const model = mapForReason(makeCaseDetail(), PHANTOM_REASON, 'LN-P2')
    expect(model.trunk.map((node) => node.key)).toEqual(['claim', 'line'])
    expect(model.trunk[1].reference?.resource_id).toBe('LN-P2')
  })

  test('one terminal per expected type, plus one per cited non-line reference', () => {
    const model = mapForReason(makeCaseDetail(), PHANTOM_REASON, 'LN-P2')
    expect(model.terminals.map((node) => [node.type, node.state])).toEqual([
      ['Encounter', 'FOUND'],
      ['Procedure', 'MISSING'],
    ])
  })

  test('a found terminal opens; an absent one is a dead end with no reference', () => {
    const model = mapForReason(makeCaseDetail(), PHANTOM_REASON, 'LN-P2')
    const encounter = model.terminals.find((node) => node.type === 'Encounter')
    const procedure = model.terminals.find((node) => node.type === 'Procedure')
    expect(encounter?.reference?.resource_id).toBe('ENC-PH-1')
    expect(procedure?.reference).toBeNull()
  })

  test('a cited reference the index cannot resolve is UNRESOLVED, the defect state', () => {
    const model = mapForReason(makeCaseDetail({ sources: [] }), PHANTOM_REASON, 'LN-P2')
    expect(model.terminals.find((node) => node.type === 'Encounter')?.state).toBe('UNRESOLVED')
  })

  test('every node key is unique — the structural form of "no node has two parents"', () => {
    const model = mapForReason(makeCaseDetail(), PHANTOM_REASON, 'LN-P2')
    expect(() => assertSinglePath(model)).not.toThrow()
    const keys = [...model.trunk, ...model.terminals].map((node) => node.key)
    expect(new Set(keys).size).toBe(keys.length)
  })

  test('two cited references of one type become two terminals, not one node with two parents', () => {
    const clone = {
      ...PHANTOM_REASON,
      code: 'NEAR_DUPLICATE_DOCUMENTATION',
      expected_support: ['Document', 'Encounter'] as const,
      evidence: [
        { resource_type: 'Document', resource_id: 'DOC-A', label: 'a' },
        { resource_type: 'Document', resource_id: 'DOC-B', label: 'b' },
        { resource_type: 'Encounter', resource_id: 'ENC-PH-1', label: 'e' },
      ] as const,
    }
    const detail = makeCaseDetail({
      reasons: [clone],
      sources: [
        ...SOURCES,
        { resource_type: 'Document', resource_id: 'DOC-A', label: 'a', availability: 'PRESENT', fields: [] },
        { resource_type: 'Document', resource_id: 'DOC-B', label: 'b', availability: 'RELATED_BUNDLE', fields: [] },
      ],
    })
    const model = mapForReason(detail, clone, null)
    const documents = model.terminals.filter((node) => node.type === 'Document')
    expect(documents.map((node) => node.reference?.resource_id)).toEqual(['DOC-A', 'DOC-B'])
    expect(() => assertSinglePath(model)).not.toThrow()
  })
})

describe('anchoring on the reason, following the line', () => {
  test('the line node follows the selected line when the reason cites it', () => {
    const model = mapForReason(makeCaseDetail(), PHANTOM_REASON, 'LN-P2')
    expect(model.trunk[1].reference?.resource_id).toBe('LN-P2')
  })

  test('a claim-level reason has a trunk that says no specific line is cited', () => {
    const model = mapForReason(makeCaseDetail({ reasons: [REPEAT_REASON] }), REPEAT_REASON, 'LN-P1')
    expect(model.trunk.map((node) => node.key)).toEqual(['claim', 'line'])
    expect(model.trunk[1].reference).toBeNull()
    expect(model.terminals.map((node) => node.type)).toEqual(['Claim'])
  })

  test('the counter-track carries the reason\'s counter-evidence notes verbatim', () => {
    const model = mapForReason(makeCaseDetail(), PHANTOM_REASON, 'LN-P2')
    expect(model.counter).toEqual(PHANTOM_REASON.counter_evidence_notes)
  })
})

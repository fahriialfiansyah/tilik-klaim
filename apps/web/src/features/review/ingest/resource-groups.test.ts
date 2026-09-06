import { describe, expect, test } from 'vitest'

import { groupResourceCounts } from '@/features/review/ingest/resource-groups'
import type { ResourceCount } from '@/features/review/ingest/types'

/** The `phantom` sample, as the API reports it. */
const PHANTOM: readonly ResourceCount[] = [
  { resource_type: 'Account', count: 1 },
  { resource_type: 'ChargeItem', count: 2 },
  { resource_type: 'Claim', count: 1 },
  { resource_type: 'ClaimLine', count: 2 },
  { resource_type: 'Condition', count: 1 },
  { resource_type: 'Diagnostic', count: 0 },
  { resource_type: 'Document', count: 0 },
  { resource_type: 'Encounter', count: 1 },
  { resource_type: 'Invoice', count: 1 },
  { resource_type: 'Medication', count: 0 },
  { resource_type: 'Procedure', count: 1 },
]

describe('groupResourceCounts', () => {
  test('splits the counts into billing, clinical, and charge groups', () => {
    // Act
    const summary = groupResourceCounts(PHANTOM)

    // Assert
    expect(summary.groups.map((group) => group.key)).toEqual(['billing', 'clinical', 'charges'])
  })

  test('orders each group so the claim is read before its billing plumbing', () => {
    // Act
    const summary = groupResourceCounts(PHANTOM)

    // Assert
    expect(summary.groups[0].counts.map((count) => count.resource_type)).toEqual([
      'Claim',
      'ClaimLine',
    ])
  })

  /**
   * The meter counts *kinds* of evidence, not records. Two charge items are one kind present,
   * because the question the panel answers is which categories arrived at all.
   */
  test('counts a type once however many records it carries', () => {
    // Act
    const summary = groupResourceCounts(PHANTOM)
    const charges = summary.groups.find((group) => group.key === 'charges')

    // Assert
    expect(charges).toMatchObject({ present: 3, total: 3 })
  })

  test('an absent type lowers the tally without leaving the list', () => {
    // Act
    const summary = groupResourceCounts(PHANTOM)
    const clinical = summary.groups.find((group) => group.key === 'clinical')

    // Assert
    expect(clinical).toMatchObject({ present: 3, total: 6 })
    expect(clinical?.counts).toHaveLength(6)
  })

  test('reports the overall tally across every group', () => {
    // Act
    const summary = groupResourceCounts(PHANTOM)

    // Assert
    expect(summary).toMatchObject({ present: 8, total: 11 })
  })

  /** A type the frontend has not been taught is still evidence that arrived. */
  test('keeps an unrecognised resource type rather than dropping it', () => {
    // Arrange
    const counts = [...PHANTOM, { resource_type: 'Appointment', count: 2 }]

    // Act
    const summary = groupResourceCounts(counts)
    const other = summary.groups.find((group) => group.key === 'other')

    // Assert
    expect(other?.counts).toEqual([{ resource_type: 'Appointment', count: 2 }])
    expect(summary.total).toBe(12)
  })

  test('omits a group the response said nothing about', () => {
    // Act
    const summary = groupResourceCounts([{ resource_type: 'Claim', count: 1 }])

    // Assert
    expect(summary.groups.map((group) => group.key)).toEqual(['billing'])
    expect(summary).toMatchObject({ present: 1, total: 1 })
  })

  test('an empty response produces an empty summary rather than throwing', () => {
    // Act & Assert
    expect(groupResourceCounts([])).toEqual({ groups: [], present: 0, total: 0 })
  })

  test('does not mutate the counts it was given', () => {
    // Arrange
    const counts: readonly ResourceCount[] = [...PHANTOM]

    // Act
    groupResourceCounts(counts)

    // Assert
    expect(counts).toEqual(PHANTOM)
  })
})

import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, test } from 'vitest'

import { ResourceSummary } from '@/features/review/ingest/components/ResourceSummary'
import type { ResourceCount } from '@/features/review/ingest/types'

/** The `phantom` sample: three clinical categories arrived, three did not. */
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

describe('the coverage summary', () => {
  /** The panel is scanned, not read: the tally has to answer "did it arrive whole" first. */
  test('leads with the overall tally', () => {
    // Act
    render(<ResourceSummary counts={PHANTOM} />)

    // Assert — the numerals sit in their own mono spans, so the assertion is on the sentence
    // the paragraph adds up to.
    expect(screen.getByText(/jenis terkirim/)).toHaveTextContent('8 dari 11 jenis terkirim')
  })

  test('gives every group its own tally', () => {
    // Act
    render(<ResourceSummary counts={PHANTOM} />)

    // Assert — the group name also heads its block in the folded detail, so the tally is the
    // unique handle here.
    expect(screen.getByText('3 / 6')).toBeVisible()
    expect(screen.getAllByText('Bukti klinis')[0]).toBeVisible()
  })

  test('an empty response renders nothing rather than an empty meter', () => {
    // Act
    const { container } = render(<ResourceSummary counts={[]} />)

    // Assert
    expect(container).toBeEmptyDOMElement()
  })
})

describe('the per-type detail', () => {
  test('is folded away so the summary is read first', () => {
    // Act
    render(<ResourceSummary counts={PHANTOM} />)

    // Assert
    expect(screen.getByText('Rincian per jenis')).toBeVisible()
    expect(screen.getByText('Obat')).not.toBeVisible()
  })

  /**
   * The row looked exactly like the group rows above it, so nothing said it could be opened.
   * A disclosure whose only affordance is the cursor is a dead end for anyone not hovering.
   */
  test('announces itself as a disclosure rather than looking like another row', () => {
    // Act
    render(<ResourceSummary counts={PHANTOM} />)
    const toggle = screen.getByText('Rincian per jenis').closest('summary')

    // Assert — a chevron to see, and the count as a second cue to what is inside.
    expect(toggle?.querySelector('svg')).toBeTruthy()
    expect(toggle).toHaveTextContent('11')
  })

  test('opens on request', async () => {
    // Arrange
    render(<ResourceSummary counts={PHANTOM} />)

    // Act
    await userEvent.click(screen.getByText('Rincian per jenis'))

    // Assert
    expect(screen.getByText('Obat')).toBeVisible()
  })

  /**
   * `design/DESIGN.md` binds this: a status must always carry a text label, never colour
   * alone — and absence here must not be drawn as a fault, because a bundle without
   * medication data is incomplete, not suspicious.
   */
  test('names an absent type in words, never colour alone', async () => {
    // Arrange
    render(<ResourceSummary counts={PHANTOM} />)

    // Act
    await userEvent.click(screen.getByText('Rincian per jenis'))

    // Assert
    expect(screen.getAllByText('tidak dikirim')).toHaveLength(3)
  })

  test('shows a zero rather than hiding the type that carries it', async () => {
    // Arrange
    render(<ResourceSummary counts={PHANTOM} />)

    // Act
    await userEvent.click(screen.getByText('Rincian per jenis'))

    // Assert
    expect(screen.getByText('Penunjang')).toBeVisible()
    expect(screen.getByText('Catatan klinis')).toBeVisible()
  })
})

import { render, screen } from '@testing-library/react'
import { describe, expect, test } from 'vitest'

import { EvidenceMeter } from '@/features/review/shared/components/EvidenceMeter'
import type { EvidenceCompleteness } from '@/features/review/shared/types'

function completeness(overrides: Partial<EvidenceCompleteness> = {}): EvidenceCompleteness {
  return {
    supported_lines: 2,
    total_lines: 2,
    missing_reference_count: 0,
    bundle_complete: true,
    ...overrides,
  }
}

/** Counts the meter segments drawn as filled rather than as empty track. */
function filledSegments(container: HTMLElement): number {
  return container.querySelectorAll('.bg-ink-2').length
}

describe('evidence meter', () => {
  test('shows how many billed lines carried support', () => {
    // Arrange & Act
    render(<EvidenceMeter completeness={completeness({ supported_lines: 1, total_lines: 2 })} />)

    // Assert
    expect(screen.getByText('1/2 baris didukung')).toBeInTheDocument()
  })

  test('no billed lines is drawn as nothing to assess, not as full support', () => {
    // Regression. With `total_lines: 0` the ratio computed as 1 and every segment filled, so a
    // case the screening never assessed rendered identically to one with complete support.
    const { container } = render(
      <EvidenceMeter completeness={completeness({ supported_lines: 0, total_lines: 0 })} />,
    )

    expect(screen.getByText('Tidak ada baris tertagih')).toBeInTheDocument()
    expect(filledSegments(container)).toBe(0)
  })

  test('an incomplete bundle reads as a thin record, never as missing evidence', () => {
    // The distinction the whole system turns on: absence in an incomplete record is not
    // evidence a service was not delivered.
    const { container } = render(
      <EvidenceMeter completeness={completeness({ bundle_complete: false })} />,
    )

    expect(screen.getByText('Berkas belum lengkap')).toBeInTheDocument()
    expect(filledSegments(container)).toBe(0)
  })

  test('full support still never renders green', () => {
    // `design/DESIGN.md` reserves green for completed, validated actions. A supported claim
    // line is not a cleared claim, and colouring it green would say it is.
    const { container } = render(<EvidenceMeter completeness={completeness()} />)

    expect(container.querySelector('[class*="done"]')).toBeNull()
    expect(container.querySelector('[class*="grn"]')).toBeNull()
  })
})

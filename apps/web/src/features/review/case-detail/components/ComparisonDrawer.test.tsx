import { screen } from '@testing-library/react'
import { describe, expect, test, vi } from 'vitest'

import { ComparisonDrawer } from '@/features/review/case-detail/components/ComparisonDrawer'
import { CLONE_COMPARISON } from '@/features/review/case-detail/test-fixtures'
import { renderWithRouter } from '@/test/render'

/**
 * The drawer names a candidate claim. Until Sprint 07 it named it and stopped there — the
 * reviewer had to go back to the queue and find that claim by hand, on the screen this project
 * treats as the most expensive to misread.
 *
 * `candidate_case_id` is legitimately null in two situations, and neither is a defect: the
 * candidate was accepted but never screened, so no case exists; or the candidate is another
 * participant's note, which cloning compares across and the service is handed without the
 * submission behind it. Both must read as "nothing to open", never as a dead link.
 */
describe('the comparison drawer offers a route to the candidate', () => {
  test('a candidate with a case is a link the reviewer can follow', () => {
    // Arrange & Act
    renderWithRouter(
      <ComparisonDrawer
        candidate={{ ...CLONE_COMPARISON, candidate_case_id: 'case_abc123' }}
        onClose={vi.fn()}
      />,
    )

    // Assert
    const link = screen.getByRole('link', { name: 'Buka kasus kandidat' })
    expect(link).toHaveAttribute('href', '/cases/case_abc123')
  })

  test('a candidate with no case says so instead of offering a dead link', () => {
    renderWithRouter(
      <ComparisonDrawer
        candidate={{ ...CLONE_COMPARISON, candidate_case_id: null }}
        onClose={vi.fn()}
      />,
    )

    expect(screen.queryByRole('link', { name: 'Buka kasus kandidat' })).not.toBeInTheDocument()
    expect(
      screen.getByText('Belum ada kasus yang bisa dibuka untuk kandidat ini.'),
    ).toBeInTheDocument()
  })

  test('the candidate claim is always named, linked or not', () => {
    renderWithRouter(
      <ComparisonDrawer candidate={{ ...CLONE_COMPARISON, candidate_case_id: null }} onClose={vi.fn()} />,
    )

    expect(screen.getByText(CLONE_COMPARISON.candidate_claim_id)).toBeInTheDocument()
  })
})

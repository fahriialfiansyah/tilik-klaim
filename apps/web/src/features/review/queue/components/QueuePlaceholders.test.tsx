import { screen } from '@testing-library/react'
import { describe, expect, test, vi } from 'vitest'

import {
  QueueEmpty,
  QueueFailed,
  QueueFilteredEmpty,
  QueueLoading,
} from '@/features/review/queue/components/QueuePlaceholders'
import { renderWithRouter } from '@/test/render'

/**
 * All four render an empty table area, and telling them apart is the whole point.
 *
 * `brief/03_ANTREAN_REVIEW.md` § 4.3 calls collapsing them the most common and most damaging
 * defect on this screen: a reviewer who cannot distinguish "no cases" from "the service is
 * down" has no way to know whether the system is working.
 */
describe('the four empty and error states are distinguishable', () => {
  test('loading announces itself as busy rather than showing a blank table', () => {
    // Arrange & Act
    renderWithRouter(<QueueLoading />)

    // Assert
    expect(screen.getByText('Memuat antrean…')).toBeInTheDocument()
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  test('no cases at all points the reviewer at Ingest', () => {
    renderWithRouter(<QueueEmpty />)

    expect(screen.getByText('Belum ada kasus sama sekali')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Masukkan bundel' })).toBeInTheDocument()
  })

  test('empty from filters names the filters responsible and offers to clear them', () => {
    const onClear = vi.fn()

    renderWithRouter(
      <QueueFilteredEmpty
        activeFilters={['pita Konflik deterministik', 'mode Dokumentasi salinan']}
        onClear={onClear}
      />,
    )

    expect(screen.getByText(/pita Konflik deterministik \+ mode Dokumentasi salinan/)).toBeInTheDocument()
    // The reassurance matters as much as the list: the data is still there.
    expect(screen.getByText(/Data tetap ada/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Bersihkan saringan' })).toBeInTheDocument()
  })

  test('a service failure says so plainly and never poses as an empty queue', () => {
    renderWithRouter(<QueueFailed error={new Error('Layanan tidak merespons')} onRetry={vi.fn()} />)

    expect(screen.getByText('Antrean tidak dapat dimuat')).toBeInTheDocument()
    expect(screen.getByText(/Ini bukan berarti tidak ada kasus/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Coba lagi/ })).toBeInTheDocument()
  })

  test('the failure and the no-cases states never share their headline', () => {
    const { unmount } = renderWithRouter(<QueueEmpty />)
    const emptyHeadline = screen.getByText('Belum ada kasus sama sekali').textContent
    unmount()

    renderWithRouter(<QueueFailed error={null} onRetry={vi.fn()} />)
    const failedHeadline = screen.getByText('Antrean tidak dapat dimuat').textContent

    expect(failedHeadline).not.toBe(emptyHeadline)
  })
})

import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, test, vi } from 'vitest'

import { EpisodeSwimlane } from '@/features/review/case-detail/components/EpisodeSwimlane'
import { makeCaseDetail } from '@/features/review/case-detail/test-fixtures'
import { renderWithRouter } from '@/test/render'

function renderLanes(detail = makeCaseDetail(), onOpenSource = vi.fn()) {
  renderWithRouter(<EpisodeSwimlane detail={detail} onOpenSource={onOpenSource} />)
  return onOpenSource
}

describe('widget 14 — the episode as swimlanes', () => {
  test('renders four lanes as rows of one table, in the fixed order', () => {
    renderLanes()

    const headers = screen.getAllByRole('rowheader').map((cell) => cell.textContent?.trim())
    expect(headers).toEqual(
      expect.arrayContaining([
        expect.stringContaining('Kunjungan'),
        expect.stringContaining('Tindakan'),
        expect.stringContaining('Obat'),
        expect.stringContaining('Penagihan'),
      ]),
    )
    expect(headers.findIndex((h) => h?.includes('Kunjungan'))).toBeLessThan(
      headers.findIndex((h) => h?.includes('Penagihan')),
    )
  })

  /**
   * The phantom picture. The billed service is in the *Penagihan* lane at 10:00 and the
   * *Tindakan* lane beside it is empty — and says so in words, because an empty row a reader
   * has to interpret is not a finding, it is a gap in the rendering.
   */
  test('an empty lane is drawn and labelled as having no recorded event', () => {
    renderLanes()

    const procedures = screen.getByRole('row', { name: /Tindakan/ })
    expect(procedures).toHaveTextContent(/tidak ada kejadian tercatat/i)
  })

  test('the billing lane carries one event per billed line, each opening its line', async () => {
    const onOpenSource = renderLanes()

    const billing = screen.getByRole('row', { name: /Penagihan/ })
    await userEvent.click(within(billing).getByRole('button', { name: /LN-P2/ }))
    expect(onOpenSource).toHaveBeenCalledWith(
      expect.objectContaining({ resource_type: 'ClaimLine', resource_id: 'LN-P2' }),
    )
  })

  test('the shared axis shows one column per distinct minute', () => {
    renderLanes()

    const times = screen.getAllByRole('columnheader').slice(1).map((cell) => cell.textContent)
    expect(times).toHaveLength(3)
  })

  test('every timeline resource still opens through the evidence reference', async () => {
    const onOpenSource = renderLanes()

    await userEvent.click(screen.getByRole('button', { name: /Kunjungan ENC-PH-1/ }))
    expect(onOpenSource).toHaveBeenCalledWith(
      expect.objectContaining({ resource_type: 'Encounter', resource_id: 'ENC-PH-1' }),
    )
  })

  test('with nothing to place in time the section says so and draws no table', () => {
    renderLanes(makeCaseDetail({ timeline: [], lines: [] }))

    expect(screen.queryByRole('table')).not.toBeInTheDocument()
    expect(screen.getByText(/tidak memuat kejadian yang dapat diurutkan/)).toBeInTheDocument()
  })
})

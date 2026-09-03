import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, test, vi } from 'vitest'

import { EvidenceMap } from '@/features/review/case-detail/components/EvidenceMap'
import { PHANTOM_REASON, makeCaseDetail } from '@/features/review/case-detail/test-fixtures'
import { renderWithRouter } from '@/test/render'

function renderMap(props: Partial<Parameters<typeof EvidenceMap>[0]> = {}) {
  const onOpenSource = vi.fn()
  renderWithRouter(
    <EvidenceMap
      detail={makeCaseDetail()}
      reason={PHANTOM_REASON}
      selectedLineId="LN-P2"
      onOpenSource={onOpenSource}
      {...props}
    />,
  )
  return onOpenSource
}

describe('widget 15 — the reason-focused evidence map', () => {
  test('draws one trunk: claim, then the cited line', () => {
    renderMap()

    const trunk = screen.getByRole('list', { name: 'Jalur klaim' })
    const items = within(trunk).getAllByRole('listitem').map((item) => item.textContent)
    expect(items[0]).toMatch(/Klaim/)
    expect(items[1]).toMatch(/Baris tagihan.*Layanan 88\.71/)
  })

  test('draws one terminal per expected type, labelled found or not found in words', () => {
    renderMap()

    const terminals = screen.getByRole('list', { name: 'Bukti yang diharapkan' })
    expect(within(terminals).getAllByRole('listitem')).toHaveLength(2)
    expect(terminals).toHaveTextContent(/Tindakan.*tidak ditemukan/)
    expect(terminals).toHaveTextContent(/Kunjungan.*ENC-PH-1/)
  })

  test('a found terminal opens its source', async () => {
    const onOpenSource = renderMap()

    // Scoped to the terminals: the counter-track cites the same visit, and that is correct —
    // the encounter both backs the reason and is where the argument against it lives.
    const terminals = screen.getByRole('list', { name: 'Bukti yang diharapkan' })
    await userEvent.click(within(terminals).getByRole('button', { name: /Kunjungan ENC-PH-1/ }))
    expect(onOpenSource).toHaveBeenCalledWith(
      expect.objectContaining({ resource_type: 'Encounter', resource_id: 'ENC-PH-1' }),
    )
  })

  test('an absent terminal is a dead end with no button', () => {
    renderMap()

    const terminals = screen.getByRole('list', { name: 'Bukti yang diharapkan' })
    const deadEnd = within(terminals).getByText(/tidak ditemukan/).closest('li')
    expect(deadEnd && within(deadEnd).queryByRole('button')).toBeNull()
  })

  /**
   * Display rule 2 restated for the map: the counter-track is *in addition* to widget 13, drawn
   * on its own labelled branch so a reader cannot mistake an argument against the reason for
   * evidence supporting it.
   */
  test('the counter-track is labelled as counter-evidence and carries the note', () => {
    renderMap()

    const counter = screen.getByRole('list', { name: 'Bukti tandingan' })
    expect(counter).toHaveTextContent(/Bundel ini hanya memuat bukti yang ikut terkirim/)
  })

  /**
   * Carried forward from `EvidencePath`: with no reason open there is no trail to follow and
   * no claim to make about what is missing. Saying "bukti klinis tidak ditemukan" on a case
   * where nothing fired is an accusation the data does not make.
   */
  test('with no reason open, the map makes no claim about missing evidence', () => {
    renderMap({ reason: null })

    expect(screen.getByText(/Belum ada alasan yang ditelusuri/)).toBeInTheDocument()
    expect(screen.queryByText(/tidak ditemukan/)).not.toBeInTheDocument()
  })
})

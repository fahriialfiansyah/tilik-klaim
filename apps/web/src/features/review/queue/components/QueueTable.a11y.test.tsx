import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, test } from 'vitest'

import { QueueTable } from '@/features/review/queue/components/QueueTable'
import { BAND_LABELS, MODE_LABELS, STATE_LABELS } from '@/features/review/shared/labels'
import { PRIORITY_BANDS, type CaseSummary } from '@/features/review/shared/types'
import { renderWithRouter } from '@/test/render'

function row(overrides: Partial<CaseSummary> = {}): CaseSummary {
  return {
    reason_sentence: 'Baris tindakan ini tidak punya catatan tindakan yang selesai.',
    modes: ['PHANTOM_OR_NO_PROCEDURE_EVIDENCE'],
    case_id: 'case_abc123',
    participant_token: 'PSN-1002',
    provider_token: 'PRV-01',
    evidence_completeness: {
      supported_lines: 0,
      total_lines: 1,
      missing_reference_count: 0,
      bundle_complete: true,
    },
    total_amount: '630000.00',
    currency: 'IDR',
    created_at: new Date().toISOString(),
    band: 'DETERMINISTIC_CONFLICT',
    state: 'SCREENED',
    case_version: 1,
    ...overrides,
  }
}

describe('queue table accessibility', () => {
  test('the reason sentence is the first column, ahead of any score or amount', () => {
    // Arrange & Act
    renderWithRouter(<QueueTable rows={[row()]} />)

    // Assert — the binding rule from brief/03 § 2.2 and § 10.3.
    const headers = screen.getAllByRole('columnheader').map((cell) => cell.textContent?.trim())
    expect(headers[0]).toBe('KALIMAT ALASAN')
    expect(headers.indexOf('NOMINAL')).toBeGreaterThan(0)
  })

  test('each row exposes exactly one tab stop, and it is a link to the case', async () => {
    const user = userEvent.setup()
    renderWithRouter(<QueueTable rows={[row({ case_id: 'case_one' }), row({ case_id: 'case_two' })]} />)

    // Two rows, two links — a tabIndex on the <tr> as well would double this and announce
    // neither target.
    const links = screen.getAllByRole('link')
    expect(links).toHaveLength(2)
    expect(links[0]).toHaveAttribute('href', '/cases/case_one')

    await user.tab()
    // The first tab lands on a sortable header or the first row link, never on a bare <tr>.
    expect(document.activeElement?.tagName).not.toBe('TR')
  })

  test('every status carries a text label, never colour alone', () => {
    renderWithRouter(
      <QueueTable rows={PRIORITY_BANDS.map((band) => row({ band, case_id: `case_${band}` }))} />,
    )

    // `design/DESIGN.md` forbids conveying status by colour alone. Reading the labels back is
    // the only check that would fail if someone replaced a badge with a coloured dot.
    for (const band of PRIORITY_BANDS) {
      expect(screen.getAllByText(BAND_LABELS[band]).length).toBeGreaterThan(0)
    }
  })

  test('a case with no signal never reads as clean or safe', () => {
    const { container } = renderWithRouter(
      <QueueTable rows={[row({ band: 'NO_OBSERVED_RISK', modes: [] })]} />,
    )

    expect(screen.getByText('Tidak ada risiko teramati')).toBeInTheDocument()

    // A bare search for the forbidden words flags the sentence that forbids them — the band's
    // own rationale ends "...bukan pernyataan bahwa klaimnya bersih", which is the safeguard,
    // not a violation. So assert on the phrase: every occurrence must sit inside a negation.
    const text = container.textContent ?? ''
    const claims = [...text.matchAll(/bersih|aman/gi)]
    expect(claims.length).toBeGreaterThan(0)
    for (const match of claims) {
      const preceding = text.slice(Math.max(0, (match.index ?? 0) - 60), match.index)
      expect(preceding).toMatch(/bukan|tidak/i)
    }
  })

  test('the band badge explains why this band, for the hover the spec requires', () => {
    renderWithRouter(<QueueTable rows={[row({ band: 'NEEDS_CONTEXT' })]} />)

    const badge = screen.getByText(BAND_LABELS.NEEDS_CONTEXT)
    expect(badge).toHaveAttribute('title', expect.stringContaining('Bukti belum cukup'))
  })

  test('mode and state render as working language, not as wire enum values', () => {
    renderWithRouter(<QueueTable rows={[row()]} />)

    const table = screen.getByRole('table', { name: 'Antrean kasus' })
    expect(within(table).getByText(MODE_LABELS.PHANTOM_OR_NO_PROCEDURE_EVIDENCE)).toBeInTheDocument()
    expect(within(table).getByText(STATE_LABELS.SCREENED)).toBeInTheDocument()
    expect(within(table).queryByText('PHANTOM_OR_NO_PROCEDURE_EVIDENCE')).not.toBeInTheDocument()
  })
})

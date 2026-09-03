import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, test, vi } from 'vitest'

import { EvidenceMatrix } from '@/features/review/case-detail/components/EvidenceMatrix'
import { MATRIX_CELL_LABELS } from '@/features/review/case-detail/labels'
import { buildEvidenceMatrix } from '@/features/review/case-detail/matrix'
import { REPEAT_REASON, makeCaseDetail } from '@/features/review/case-detail/test-fixtures'
import { renderWithRouter } from '@/test/render'

function renderMatrix(detail = makeCaseDetail(), props: Partial<Parameters<typeof EvidenceMatrix>[0]> = {}) {
  return renderWithRouter(
    <EvidenceMatrix
      matrix={buildEvidenceMatrix(detail)}
      sources={detail.sources}
      selectedLineId={null}
      openReasonCode={null}
      onSelectLine={vi.fn()}
      onOpenSource={vi.fn()}
      {...props}
    />,
  )
}

function cellFor(rowName: RegExp, columnName: string) {
  const rowElement = screen.getByRole('row', { name: rowName })
  const headers = screen.getAllByRole('columnheader').map((cell) => cell.textContent?.trim() ?? '')
  const index = headers.indexOf(columnName)
  expect(index, `column ${columnName}`).toBeGreaterThan(0)
  return within(rowElement).getAllByRole('cell')[index - 1]
}

describe('widget 28 — the evidence matrix', () => {
  test('is a real table with a header row and a row header per billed line', () => {
    renderMatrix()

    expect(screen.getByRole('table', { name: 'Matriks bukti' })).toBeInTheDocument()
    expect(screen.getByRole('rowheader', { name: /Layanan 88\.71/ })).toBeInTheDocument()
  })

  test('the phantom cell reads "tidak ditemukan" in words, not only in colour', () => {
    renderMatrix()

    expect(cellFor(/Layanan 88\.71/, 'Tindakan')).toHaveTextContent(MATRIX_CELL_LABELS.MISSING)
  })

  /**
   * ADR-0004's fourth state. The untouched line's cells must say nobody expected anything
   * there — to a sighted reader they are quiet, to a screen reader they are explicit, and in
   * neither case do they read as "absent".
   */
  test('a NOT_EXPECTED cell is labelled for assistive technology and never says "tidak ditemukan"', () => {
    renderMatrix()

    const quiet = cellFor(/Layanan 89\.7/, 'Tindakan')
    expect(quiet).toHaveTextContent(MATRIX_CELL_LABELS.NOT_EXPECTED)
    expect(quiet).not.toHaveTextContent(MATRIX_CELL_LABELS.MISSING)
  })

  test('an UNRESOLVED cell is the defect, worded as such', () => {
    renderMatrix(makeCaseDetail({ sources: [] }))

    expect(cellFor(/Layanan 88\.71/, 'Kunjungan')).toHaveTextContent(MATRIX_CELL_LABELS.UNRESOLVED)
  })

  test('a found reference is an openable button that goes through the source index', async () => {
    const onOpenSource = vi.fn()
    renderMatrix(makeCaseDetail(), { onOpenSource })

    await userEvent.click(within(cellFor(/Layanan 88\.71/, 'Kunjungan')).getByRole('button', { name: /ENC-PH-1/ }))
    expect(onOpenSource).toHaveBeenCalledWith(
      expect.objectContaining({ resource_type: 'Encounter', resource_id: 'ENC-PH-1' }),
    )
  })

  test('the row header selects the line', async () => {
    const onSelectLine = vi.fn()
    renderMatrix(makeCaseDetail(), { onSelectLine })

    await userEvent.click(screen.getByRole('button', { name: /Layanan 88\.71/ }))
    expect(onSelectLine).toHaveBeenCalledWith('LN-P2')
  })

  test('the selected row is announced as pressed', () => {
    renderMatrix(makeCaseDetail(), { selectedLineId: 'LN-P2' })

    expect(screen.getByRole('button', { name: /Layanan 88\.71/ })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: /Layanan 89\.7/ })).toHaveAttribute('aria-pressed', 'false')
  })

  test('a claim-level reason gets a row that says it cites no particular line', () => {
    renderMatrix(makeCaseDetail({ reasons: [REPEAT_REASON] }))

    expect(screen.getByRole('rowheader', { name: /Tingkat klaim/ })).toBeInTheDocument()
    expect(cellFor(/Tingkat klaim/, 'Klaim')).toHaveTextContent(MATRIX_CELL_LABELS.FOUND)
  })

  test('with no reasons the matrix says nothing was observed, never "bersih" or "aman"', () => {
    renderMatrix(makeCaseDetail({ reasons: [], primary_reason: null }))

    const region = screen.getByRole('region', { name: 'Matriks bukti' })
    expect(region).toHaveTextContent(/tidak ada risiko teramati/i)
    expect(region).not.toHaveTextContent(/bersih|aman/i)
  })

  test('with no billed lines the matrix says so', () => {
    renderMatrix(makeCaseDetail({ lines: [] }))

    expect(screen.getByRole('region', { name: 'Matriks bukti' })).toHaveTextContent(
      /tidak memuat baris tagihan/,
    )
  })
})

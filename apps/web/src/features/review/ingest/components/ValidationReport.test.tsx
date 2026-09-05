import { screen } from '@testing-library/react'
import { describe, expect, test, vi } from 'vitest'

import { ValidationReport } from '@/features/review/ingest/components/ValidationReport'
import type { BundleRejection } from '@/features/review/ingest/rejection'
import type { IngestBundleResponse, ValidationStatus } from '@/features/review/ingest/types'
import { renderWithRouter } from '@/test/render'

function makeReport(overrides: Partial<IngestBundleResponse> = {}): IngestBundleResponse {
  return {
    ingestion_id: 'ing_1',
    status: 'VALID',
    input_hash: 'a'.repeat(64),
    resource_counts: [
      { resource_type: 'Claim', count: 1 },
      { resource_type: 'ClaimLine', count: 2 },
      { resource_type: 'Procedure', count: 0 },
    ],
    issues: [],
    completeness_notes: [],
    is_screenable: true,
    existing_case_id: null,
    schema_version: '0.1.0',
    ...overrides,
  }
}

function render(
  report: IngestBundleResponse | null,
  rejection: BundleRejection | null = null,
) {
  return renderWithRouter(
    <ValidationReport
      report={report}
      rejection={rejection}
      screenStatus="idle"
      onScreen={vi.fn()}
    />,
  )
}

function screenButton() {
  return screen.getByRole('button', { name: 'Saring klaim' })
}

describe('the three validation states are drawn distinctly', () => {
  const cases: readonly [ValidationStatus, string][] = [
    ['VALID', 'Sah'],
    ['VALID_WITH_NOTES', 'Sah dengan catatan'],
    ['INVALID', 'Tidak sah'],
  ]

  test.each(cases)('%s reads as "%s"', (status, label) => {
    render(makeReport({ status, is_screenable: status !== 'INVALID' }))
    expect(screen.getByText(label)).toBeVisible()
  })

  /**
   * `VALID_WITH_NOTES` is **not** a softer `INVALID`. An incomplete record and a
   * billed-but-unevidenced service look identical at the schema level, and this is the screen
   * where they first have to be told apart — so a bundle with notes still screens.
   */
  test('valid-with-notes still screens, because a thin record is not a rejected one', () => {
    render(makeReport({ status: 'VALID_WITH_NOTES', completeness_notes: ['Tidak ada tindakan.'] }))
    expect(screenButton()).toBeEnabled()
  })

  test('invalid disables the button and states the reason', () => {
    render(makeReport({ status: 'INVALID', is_screenable: false }))

    expect(screenButton()).toBeDisabled()
    expect(screen.getByText(/tidak dapat disaring/)).toBeVisible()
    expect(screen.getByText(/tidak ada penyaringan sebagian/i)).toBeVisible()
  })
})

describe('the empty state', () => {
  test('says nothing has been checked rather than showing a blank report', () => {
    render(null)

    expect(screen.getByText('Belum ada berkas')).toBeVisible()
    expect(screen.getByText('Belum diperiksa')).toBeVisible()
    expect(screen.queryByRole('button', { name: 'Saring klaim' })).not.toBeInTheDocument()
  })
})

describe('a refused bundle', () => {
  const refusal: BundleRejection = {
    code: 'BUNDLE_MALFORMED_JSON',
    message: 'Isi berkas bukan JSON yang sah.',
    issues: [],
    source: 'server',
  }

  /**
   * A pre-parse refusal arrives as a `4xx` envelope rather than a `200` report. Leaving the
   * panel on "belum diperiksa" while an error sits above it would have two parts of the screen
   * disagreeing about whether anything was checked.
   */
  test('is reported as invalid, with its stable code', () => {
    render(null, refusal)

    expect(screen.getByText('Tidak sah')).toBeVisible()
    expect(screen.getByText('BUNDLE_MALFORMED_JSON')).toBeVisible()
    expect(screen.getByText(refusal.message)).toBeVisible()
  })

  test('keeps the button in place, disabled, rather than removing it', () => {
    render(null, refusal)
    expect(screenButton()).toBeDisabled()
  })

  test('says whether the browser or the service refused it', () => {
    render(null, { ...refusal, source: 'client', code: 'TOO_LARGE' })
    expect(screen.getByText(/ditolak di peramban dan tidak dikirim/)).toBeVisible()
  })
})

describe('resource counts', () => {
  test('a zero count is shown rather than omitted — absence is information', () => {
    render(makeReport())

    const counts = screen.getByLabelText('Laporan validasi')
    expect(counts).toHaveTextContent('Tindakan')
    expect(counts).toHaveTextContent('0')
  })
})

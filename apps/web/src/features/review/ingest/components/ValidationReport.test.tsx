import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, test, vi } from 'vitest'

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

afterEach(() => {
  Object.defineProperty(navigator, 'clipboard', { value: undefined, configurable: true })
  Object.defineProperty(document, 'execCommand', { value: undefined, configurable: true })
})

describe('the three validation states are drawn distinctly', () => {
  const cases: readonly [ValidationStatus, string][] = [
    ['VALID', 'Valid'],
    ['VALID_WITH_NOTES', 'Valid dengan catatan'],
    ['INVALID', 'Tidak valid'],
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
  test('is reported as invalid, in a sentence rather than a code', () => {
    render(null, refusal)

    expect(screen.getByText('Tidak valid')).toBeVisible()
    expect(screen.getByText(refusal.message)).toBeVisible()
  })

  /** The machine token is reachable for a ticket, but it never leads the reading. */
  test('keeps the stable code behind the technical disclosure', async () => {
    render(null, refusal)

    expect(screen.getByText('BUNDLE_MALFORMED_JSON')).not.toBeVisible()
    await userEvent.click(screen.getByText('Detail teknis'))
    expect(screen.getByText('BUNDLE_MALFORMED_JSON')).toBeVisible()
  })

  test('keeps the button in place, disabled, rather than removing it', () => {
    render(null, refusal)
    expect(screenButton()).toBeDisabled()
  })

  test('says whether the browser or the service refused it', () => {
    render(null, { ...refusal, source: 'client', code: 'TOO_LARGE' })
    expect(screen.getByText(/ditolak di browser dan tidak dikirim/)).toBeVisible()
  })
})

describe('resource counts', () => {
  test('leads with the tally rather than eleven equal numbers', () => {
    render(makeReport())

    expect(screen.getByText(/jenis terkirim/)).toHaveTextContent('2 dari 3 jenis terkirim')
  })

  test('a zero count is shown rather than omitted — absence is information', async () => {
    render(makeReport())

    await userEvent.click(screen.getByText('Rincian per jenis'))
    expect(screen.getByText('Tindakan')).toBeVisible()
    expect(screen.getByText('tidak dikirim')).toBeVisible()
  })
})

describe('the input hash', () => {
  /** 64 characters wrapped onto two lines and dominated the panel; the prefix identifies it. */
  test('is shown as a short prefix, with the whole value kept on the element', () => {
    render(makeReport())

    const shown = screen.getByText(`sha256:${'a'.repeat(12)}…`)
    expect(shown).toBeVisible()
    expect(shown).toHaveAttribute('title', 'a'.repeat(64))
  })

  test('copies the full hash, not the prefix that is on screen', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined)
    Object.defineProperty(navigator, 'clipboard', { value: { writeText }, configurable: true })
    render(makeReport())

    await userEvent.click(screen.getByRole('button', { name: 'Salin' }))

    expect(writeText).toHaveBeenCalledWith('a'.repeat(64))
    expect(await screen.findByRole('button', { name: 'Tersalin' })).toBeVisible()
  })

  /**
   * The demo is opened over plain HTTP on a LAN address, where `navigator.clipboard` does not
   * exist. The old button swallowed that and looked broken; it has to say so.
   */
  test('reports a copy that did not happen instead of staying silent', async () => {
    render(makeReport())

    await userEvent.click(screen.getByRole('button', { name: 'Salin' }))

    expect(await screen.findByRole('button', { name: 'Gagal menyalin' })).toBeVisible()
  })
})

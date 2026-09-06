import { screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, test, vi } from 'vitest'

import {
  DuplicateBanner,
  ServiceErrorBanner,
} from '@/features/review/ingest/components/IngestBanners'
import i18n from '@/modules/i18n/config'
import { DEFAULT_LOCALE } from '@/modules/i18n/locales'
import { renderWithRouter } from '@/test/render'

const HASH = 'a'.repeat(64)

afterEach(async () => {
  await i18n.changeLanguage(DEFAULT_LOCALE)
})

/**
 * These two banners kept their sentences in the JSX rather than the locale files, so they
 * stayed Indonesian with the interface set to English — the one place a reader is *most* likely
 * to be a visitor, since the banner explains why their second submission produced no new case.
 */
describe('the duplicate banner', () => {
  test('its sentence follows the interface language', async () => {
    renderWithRouter(<DuplicateBanner caseId="case_1" inputHash={HASH} />)
    expect(screen.getByText(/sudah menghasilkan sebuah kasus/)).toBeInTheDocument()

    await i18n.changeLanguage('en')

    await waitFor(() =>
      expect(screen.getByText(/has already produced a case/)).toBeInTheDocument(),
    )
    expect(screen.queryByText(/sudah menghasilkan sebuah kasus/)).not.toBeInTheDocument()
  })

  /** The hash sits mid-sentence, so it has to survive translation rather than be concatenated. */
  test('keeps the short fingerprint inside the sentence, in both languages', async () => {
    renderWithRouter(<DuplicateBanner caseId="case_1" inputHash={HASH} />)
    expect(screen.getByText(`sha256:${'a'.repeat(12)}…`)).toBeInTheDocument()

    await i18n.changeLanguage('en')

    await waitFor(() =>
      expect(screen.getByText(`sha256:${'a'.repeat(12)}…`)).toBeInTheDocument(),
    )
  })
})

describe('the service error banner', () => {
  test('its retry button follows the interface language', async () => {
    renderWithRouter(
      <ServiceErrorBanner title="Layanan gagal" error={null} onRetry={vi.fn()} />,
    )
    expect(screen.getByRole('button', { name: 'Coba lagi' })).toBeInTheDocument()

    await i18n.changeLanguage('en')

    await waitFor(() =>
      expect(screen.getByRole('button', { name: 'Try again' })).toBeInTheDocument(),
    )
  })
})

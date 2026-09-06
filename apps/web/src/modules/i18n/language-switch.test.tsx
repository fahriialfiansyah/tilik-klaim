import { screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, test } from 'vitest'

import { BandBadge } from '@/features/review/shared/components/BandBadge'
import { EvidenceMeter } from '@/features/review/shared/components/EvidenceMeter'
import i18n from '@/modules/i18n/config'
import { DEFAULT_LOCALE } from '@/modules/i18n/locales'
import { renderWithRouter } from '@/test/render'

/**
 * Switching the language must re-render what is already on screen.
 *
 * This is the property the whole label layer was reshaped for. Every `*_LABELS` record in this
 * app used to be a module-level constant, and a constant is read **once**, at module load — so
 * a switch would change the header's own words and leave every table, badge and meter in the
 * language the bundle happened to start in. Turning them into hooks is what makes the switch
 * reach the screen, and this test is what keeps anyone from turning one back.
 */

afterEach(async () => {
  await i18n.changeLanguage(DEFAULT_LOCALE)
})

describe('a language change reaches components already rendered', () => {
  test('an enum label re-renders rather than keeping the language it mounted in', async () => {
    renderWithRouter(<BandBadge band="NEEDS_CONTEXT" />)
    expect(screen.getByText('Perlu konteks')).toBeInTheDocument()

    await i18n.changeLanguage('en')

    await waitFor(() => expect(screen.getByText('Needs context')).toBeInTheDocument())
    expect(screen.queryByText('Perlu konteks')).not.toBeInTheDocument()
  })

  test('an interpolated sentence re-renders with its numbers intact', async () => {
    renderWithRouter(
      <EvidenceMeter
        completeness={{
          supported_lines: 1,
          total_lines: 2,
          bundle_complete: true,
          missing_reference_count: 0,
        }}
      />,
    )
    expect(screen.getByText('1/2 baris didukung')).toBeInTheDocument()

    await i18n.changeLanguage('en')

    await waitFor(() => expect(screen.getByText('1/2 lines supported')).toBeInTheDocument())
  })

  test('the band rationale follows too, not only the band name', async () => {
    // The rationale is what keeps the band from reading as a verdict. A translated name over an
    // untranslated explanation would be the worst of both.
    renderWithRouter(<BandBadge band="NO_OBSERVED_RISK" />)

    await i18n.changeLanguage('en')

    await waitFor(() =>
      expect(screen.getByText(/No detector fired at this engine version/)).toBeInTheDocument(),
    )
  })

  test('neither language names the quiet band "clean"', async () => {
    // `PriorityBand.NO_OBSERVED_RISK` says what was looked for and not found. The *name* may
    // never claim more than that in either language.
    //
    // The rationale beside it is the opposite case and is checked separately below: it contains
    // the word "bersih" / "clean" on purpose, to deny the claim. A blanket word ban here would
    // have failed on the very sentence that exists to prevent the overreach — which is why this
    // asserts on the label alone.
    renderWithRouter(<BandBadge band="NO_OBSERVED_RISK" />)
    expect(screen.getByText('Tidak ada risiko teramati')).toBeInTheDocument()

    await i18n.changeLanguage('en')

    await waitFor(() => expect(screen.getByText('No risk observed')).toBeInTheDocument())
    expect(screen.queryByText(/^(clean|safe)$/i)).not.toBeInTheDocument()
  })

  test('the rationale denies the clean reading in both languages', async () => {
    renderWithRouter(<BandBadge band="NO_OBSERVED_RISK" />)
    expect(document.body.textContent ?? '').toMatch(/bukan pernyataan bahwa klaimnya bersih/i)

    await i18n.changeLanguage('en')

    await waitFor(() =>
      expect(document.body.textContent ?? '').toMatch(
        /not a statement that the claim is clean/i,
      ),
    )
  })
})

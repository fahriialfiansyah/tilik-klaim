import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, test } from 'vitest'

import { CaseHeader } from '@/features/review/case-detail/components/CaseHeader'
import { EvidenceMatrix } from '@/features/review/case-detail/components/EvidenceMatrix'
import { CLAIM_ROW_KEY, type EvidenceMatrix as EvidenceMatrixModel } from '@/features/review/case-detail/matrix'
import { makeCaseDetail } from '@/features/review/case-detail/test-fixtures'
import i18n from '@/modules/i18n/config'
import { DEFAULT_LOCALE } from '@/modules/i18n/locales'
import { renderWithRouter } from '@/test/render'

/**
 * The Evidence Workspace (ADR-0004) landed before the bilingual pass and kept several of its
 * sentences in the JSX. Those are exactly the sentences that carry the product's most careful
 * claims — what the matrix does *not* assert, what an empty cell means — so leaving them in one
 * language stranded the reader most likely to misread them.
 */

afterEach(async () => {
  await i18n.changeLanguage(DEFAULT_LOCALE)
})

/** No reasons opened yet: no columns, and only the claim-level row. */
const NO_REASONS: EvidenceMatrixModel = {
  columns: [],
  rows: [{ key: CLAIM_ROW_KEY, line: null, reasonCodes: [], cells: [] }],
}

function renderMatrix(matrix: EvidenceMatrixModel) {
  return renderWithRouter(
    <EvidenceMatrix
      matrix={matrix}
      sources={[]}
      selectedLineId={null}
      openReasonCode={null}
      onSelectLine={() => {}}
      onOpenSource={() => {}}
    />,
  )
}

describe('the evidence matrix panel', () => {
  test('its lede follows the interface language', async () => {
    renderMatrix(NO_REASONS)
    expect(screen.getByText(/Sel kosong berarti tidak ada yang diharapkan/)).toBeInTheDocument()

    await i18n.changeLanguage('en')

    await waitFor(() =>
      expect(screen.getByText(/An empty cell means nothing was expected/)).toBeInTheDocument(),
    )
  })

  /**
   * The most consequential sentence on the panel: it says the absence of a mapping is not a
   * statement about the claim. Untranslated, it is the one a visitor would have to guess at.
   */
  test('the no-reasons notice follows the interface language', async () => {
    renderMatrix({
      columns: [],
      rows: [
        ...NO_REASONS.rows,
        { key: 'LN-1', line: null, reasonCodes: [], cells: [] },
      ],
    })
    expect(screen.getByText(/bukan pernyataan tentang klaimnya/)).toBeInTheDocument()

    await i18n.changeLanguage('en')

    await waitFor(() =>
      expect(screen.getByText(/not a statement about the claim/)).toBeInTheDocument(),
    )
  })
})

describe('the case header', () => {
  /**
   * The band caveat is the single most consequential sentence in the product: it says the band
   * raises priority and does *not* allege fraud. It sat in the JSX, spliced onto a
   * server-supplied basis, so an English reader saw the basis translated and the disclaimer not.
   */
  test('the band caveat follows the interface language, keeping its basis', async () => {
    renderWithRouter(<CaseHeader detail={makeCaseDetail()} onPickAction={() => {}} />)
    await userEvent.click(screen.getByRole('button', { name: /Dasar keyakinan/ }))
    expect(screen.getByText(/bukan menyatakan fraud/)).toBeInTheDocument()

    await i18n.changeLanguage('en')

    await waitFor(() => expect(screen.getByText(/does not allege fraud/)).toBeInTheDocument())
    // The basis itself comes from the service already localised; the caveat is spliced onto it
    // rather than replacing it.
    expect(screen.getByText(/prioritas mengikuti alasan terkuat/)).toBeInTheDocument()
  })

  test('its fixed labels follow the interface language too', async () => {
    renderWithRouter(<CaseHeader detail={makeCaseDetail()} onPickAction={() => {}} />)
    expect(screen.getByText('DATA SINTETIK')).toBeInTheDocument()
    expect(screen.getByText('PESERTA · FASILITAS')).toBeInTheDocument()

    await i18n.changeLanguage('en')

    await waitFor(() => expect(screen.getByText('SYNTHETIC DATA')).toBeInTheDocument())
    expect(screen.getByText('MEMBER · FACILITY')).toBeInTheDocument()
  })
})

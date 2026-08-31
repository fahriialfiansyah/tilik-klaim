import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, test, vi } from 'vitest'

import { EvidenceRefButton } from '@/features/review/case-detail/components/EvidenceRefButton'
import { ReasonCard } from '@/features/review/case-detail/components/ReasonCard'
import { reasonStrength } from '@/features/review/case-detail/labels'
import { PHANTOM_REASON, SOURCES } from '@/features/review/case-detail/test-fixtures'
import { renderWithRouter } from '@/test/render'

function renderCard(props: Partial<Parameters<typeof ReasonCard>[0]> = {}) {
  return renderWithRouter(
    <ReasonCard
      reason={PHANTOM_REASON}
      isOpen={false}
      onToggle={vi.fn()}
      sources={SOURCES}
      onOpenSource={vi.fn()}
      onCompare={null}
      {...props}
    />,
  )
}

describe('display rule 2 — counter-evidence has equal standing', () => {
  /**
   * `sprint/00-app-spec.md` § 4 rule 2 forbids putting widget 13 behind a collapsed panel. A
   * panel the reviewer has to open first does not have equal standing with the supporting
   * evidence — it has whatever standing curiosity gives it, and this is the one screen where a
   * reviewer deciding without the argument against a signal is the failure mode that matters.
   */
  test('the counter-evidence sentence is visible while the card is collapsed', () => {
    renderCard({ isOpen: false })

    expect(screen.getByText(/Bundel ini hanya memuat bukti yang ikut terkirim/)).toBeVisible()
  })

  test('the supporting evidence is behind the collapse, and the counter-evidence is not', () => {
    renderCard({ isOpen: false })

    expect(screen.queryByText('BUKTI YANG DITEMUKAN')).not.toBeInTheDocument()
    expect(screen.getByText(/MELEMAHKAN ALASAN INI/)).toBeVisible()
  })

  test('a reason with no counter-evidence says so rather than dropping the section', () => {
    renderCard({ reason: { ...PHANTOM_REASON, counter_evidence_notes: [] } })

    expect(screen.getByText(/MELEMAHKAN ALASAN INI/)).toBeVisible()
    expect(screen.getByText(/Tidak ditemukan bukti tandingan/)).toBeVisible()
  })
})

describe('expected against found evidence', () => {
  test('names the expected resource the reason did not find', () => {
    renderCard({ isOpen: true })

    const expected = screen.getByText('BUKTI YANG DIHARAPKAN').closest('div')
    expect(expected).toHaveTextContent('Tindakan')
    expect(expected).toHaveTextContent('tidak ditemukan')
  })

  test('marks the expected resource that was found', () => {
    renderCard({ isOpen: true })

    const expected = screen.getByText('BUKTI YANG DIHARAPKAN').closest('div')
    expect(expected).toHaveTextContent('Kunjungan')
    expect(expected).toHaveTextContent('ditemukan')
  })
})

describe('evidence strength', () => {
  test('a deterministic reason with counter-evidence does not read as the strongest', () => {
    expect(reasonStrength(PHANTOM_REASON)).toBe(2)
  })

  test('a deterministic reason with nothing against it reads strongest', () => {
    expect(reasonStrength({ ...PHANTOM_REASON, counter_evidence_notes: [] })).toBe(3)
  })

  test('a scored reason with counter-evidence reads weakest', () => {
    expect(reasonStrength({ ...PHANTOM_REASON, deterministic: false })).toBe(1)
  })
})

describe('display rule 4 — every evidence reference opens', () => {
  test('a resolvable reference is a button that opens the source panel', async () => {
    const onOpen = vi.fn()
    renderWithRouter(
      <EvidenceRefButton
        reference={PHANTOM_REASON.evidence[0]}
        sources={SOURCES}
        onOpen={onOpen}
      />,
    )

    await userEvent.click(screen.getByRole('button', { name: /Baris tagihan LN-P2/ }))
    expect(onOpen).toHaveBeenCalledWith(PHANTOM_REASON.evidence[0])
  })

  /**
   * A reference the index cannot resolve is an evidence-integrity defect, not an empty panel.
   * Rendering it as a working link that opens nothing is the exact failure the rule names — the
   * reviewer clicks, sees nothing, and concludes the evidence is simply absent.
   */
  test('an unresolvable reference is flagged as a defect and is not clickable', () => {
    renderWithRouter(
      <EvidenceRefButton
        reference={{ resource_type: 'Procedure', resource_id: 'GONE', label: 'Procedure GONE' }}
        sources={SOURCES}
        onOpen={vi.fn()}
      />,
    )

    expect(screen.getByTestId('evidence-ref-broken')).toHaveTextContent('cacat integritas bukti')
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  test('a reference the store resolved as MISSING is flagged the same way', () => {
    renderWithRouter(
      <EvidenceRefButton
        reference={{ resource_type: 'Procedure', resource_id: 'P9', label: 'Procedure P9' }}
        sources={[
          {
            resource_type: 'Procedure',
            resource_id: 'P9',
            label: 'Procedure P9',
            availability: 'MISSING',
            fields: [],
          },
        ]}
        onOpen={vi.fn()}
      />,
    )

    expect(screen.getByTestId('evidence-ref-broken')).toBeVisible()
  })

  test('a peer-bundle reference still opens, and says which side it belongs to', () => {
    renderWithRouter(
      <EvidenceRefButton
        reference={{ resource_type: 'Document', resource_id: 'DOC-CL-1', label: 'x' }}
        sources={[
          {
            resource_type: 'Document',
            resource_id: 'DOC-CL-1',
            label: 'Document DOC-CL-1',
            availability: 'RELATED_BUNDLE',
            fields: [{ name: 'kind', value: 'clinical-note' }],
          },
        ]}
        onOpen={vi.fn()}
      />,
    )

    expect(screen.getByRole('button')).toHaveTextContent('bundel pembanding')
  })
})

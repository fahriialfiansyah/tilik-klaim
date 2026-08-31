import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createRef } from 'react'
import { beforeEach, describe, expect, test, vi } from 'vitest'

import { DispositionPanel } from '@/features/review/case-detail/components/DispositionPanel'
import { useCaseDetailStore } from '@/features/review/case-detail/store'
import { makeCaseDetail } from '@/features/review/case-detail/test-fixtures'
import { renderWithRouter } from '@/test/render'

function renderPanel(onSave = vi.fn()) {
  return renderWithRouter(
    <DispositionPanel
      detail={makeCaseDetail()}
      saveStatus="idle"
      onSave={onSave}
      panelRef={createRef<HTMLDivElement>()}
    />,
  )
}

function saveButton() {
  return screen.getByRole('button', { name: /Simpan disposisi/ })
}

beforeEach(() => {
  useCaseDetailStore.setState({ drafts: {} })
})

describe('save is gated on an action and a reason', () => {
  test('starts disabled and says which field is missing', () => {
    renderPanel()

    expect(saveButton()).toBeDisabled()
    expect(screen.getByText(/Pilih satu tindakan/)).toBeVisible()
  })

  test('stays disabled after an action alone, and names the reason as missing', async () => {
    renderPanel()
    await userEvent.click(screen.getByRole('radio', { name: /Eskalasi/ }))

    expect(saveButton()).toBeDisabled()
    expect(screen.getByText(/Tidak ada disposisi tanpa alasan/)).toBeVisible()
  })

  test('enables once an action and a reason are both chosen', async () => {
    renderPanel()
    await userEvent.click(screen.getByRole('radio', { name: /Eskalasi/ }))
    await userEvent.selectOptions(
      screen.getByLabelText('ALASAN TERSTRUKTUR'),
      'Perlu penelusuran oleh unit berwenang',
    )

    expect(saveButton()).toBeEnabled()
  })

  test('the reason list is disabled until an action is chosen', () => {
    renderPanel()

    expect(screen.getByLabelText('ALASAN TERSTRUKTUR')).toBeDisabled()
  })
})

describe('the system suggests and never chooses', () => {
  /**
   * `brief/04_DETAIL_KASUS_DISPOSISI.md` § 7: the interface may offer standard reasons and may
   * never pre-select one. An auto-filled reason plus an enabled save button is a decision the
   * system made and attributed to a person.
   */
  test('no action is pre-selected on load', () => {
    renderPanel()

    for (const radio of screen.getAllByRole('radio')) {
      expect(radio).not.toBeChecked()
    }
  })

  test('no reason is pre-selected once an action is chosen', async () => {
    renderPanel()
    await userEvent.click(screen.getByRole('radio', { name: /Konfirmasi anomali/ }))

    expect(screen.getByLabelText('ALASAN TERSTRUKTUR')).toHaveValue('')
  })
})

describe('requested evidence', () => {
  test('appears only for "minta bukti tambahan"', async () => {
    renderPanel()
    expect(screen.queryByText('BUKTI YANG DIMINTA')).not.toBeInTheDocument()

    await userEvent.click(screen.getByRole('radio', { name: /Minta bukti tambahan/ }))
    expect(screen.getByText('BUKTI YANG DIMINTA')).toBeVisible()
  })

  test('pre-checks the missing resource type and leaves it editable', async () => {
    renderPanel()
    await userEvent.click(screen.getByRole('radio', { name: /Minta bukti tambahan/ }))

    const procedure = screen.getByRole('checkbox', { name: 'Tindakan' })
    expect(procedure).toBeChecked()

    await userEvent.click(procedure)
    expect(procedure).not.toBeChecked()
  })
})

describe('what the panel tells the reviewer', () => {
  test('names the case version the decision is being made against', () => {
    renderPanel()

    expect(screen.getByText(/versi kasus/)).toHaveTextContent('1')
  })

  test('says plainly that confirming an anomaly is not a fraud finding', () => {
    renderPanel()

    expect(screen.getByText(/Ini bukan temuan fraud/)).toBeVisible()
  })

  test('the whole panel is reachable and operable from the keyboard', async () => {
    renderPanel()
    const first = screen.getByRole('radio', { name: /Tolak sinyal/ })

    first.focus()
    await userEvent.keyboard('{ }')
    expect(first).toBeChecked()
  })
})

import { expect, test } from '@playwright/test'

import {
  dispositionAsAnotherReviewer,
  fillDisposition,
  findOpenCase,
} from './helpers'

/**
 * The three paths `sprint/backlog/04-review-slice/frontend/02-detail-kasus.md` names, run
 * against the real API and a seeded database.
 *
 * Mocking the write path would defeat the purpose. Two of these three assert things that only
 * exist because a real server refused something — a version conflict, and an audit event that
 * was actually persisted — and against a mock both would pass with the write path broken.
 */

test.describe('happy path — queue to disposition to audit', () => {
  test('a phantom case can be confirmed and the decision appears in its history', async ({
    page,
    request,
  }) => {
    const target = await findOpenCase(request, 'PHANTOM_OR_NO_PROCEDURE_EVIDENCE')

    // Entered from the queue, as a reviewer would.
    await page.goto('/')
    await page.getByRole('link', { name: /tidak punya catatan tindakan/ }).first().click()
    await expect(page).toHaveURL(/\/cases\/case_/)

    // Reason before score: the sentence is the page heading, the band sits under it.
    await expect(page.getByRole('heading', { level: 1 })).toContainText(
      'tidak punya catatan tindakan yang selesai',
    )

    await page.goto(`/cases/${target.case_id}`)
    await fillDisposition(page, {
      action: 'Konfirmasi anomali',
      reason: 'Baris tertagih tanpa bukti layanan yang selesai',
      note: 'Diperiksa manual terhadap berkas fisik.',
    })

    // Confirming an anomaly must state that this is not a fraud finding, before it is recorded.
    await page.getByRole('button', { name: 'Simpan disposisi' }).click()
    const dialog = page.getByRole('dialog')
    await expect(dialog).toContainText('ini bukan temuan fraud')
    await expect(dialog).toContainText('Klaim tidak ditolak')
    await dialog.getByRole('button', { name: /Saya paham/ }).click()

    // A saved disposition returns to the queue.
    await expect(page).toHaveURL(/localhost:\d+\/$/)

    await page.goto(`/cases/${target.case_id}`)
    await page.getByRole('tab', { name: 'Riwayat audit' }).click()
    const history = page.getByRole('region', { name: 'Riwayat audit' })
    await expect(history).toContainText('Konfirmasi anomali')
    await expect(history).toContainText('Baris tertagih tanpa bukti layanan yang selesai')
    await expect(history).toContainText('Diperiksa manual terhadap berkas fisik.')
  })
})

test.describe('false-positive path — counter-evidence leads to rejecting the signal', () => {
  test('the argument against a repeat-billing signal is on screen without being opened', async ({
    page,
    request,
  }) => {
    const target = await findOpenCase(request, 'REPEAT_BILLING')
    await page.goto(`/cases/${target.case_id}`)

    // Display rule 2: counter-evidence is never behind a collapsed panel. Collapse the reason
    // card and the argument against it must still be readable.
    const card = page.getByRole('button', { name: /kekuatan/ }).first()
    await card.click()
    await expect(card).toHaveAttribute('aria-expanded', 'false')
    await expect(page.getByText('BUKTI TANDINGAN — MELEMAHKAN ALASAN INI')).toBeVisible()
    await expect(page.getByText(/Bidang berikut berbeda antara kedua klaim/)).toBeVisible()

    // The comparison drawer confirms which fields actually differ.
    await card.click()
    await page.getByRole('button', { name: 'Bandingkan pasangan kandidat' }).click()
    const drawer = page.getByRole('dialog')
    await expect(drawer).toContainText('BIDANG YANG DIBANDINGKAN')
    await expect(drawer.getByText('berbeda').first()).toBeVisible()
    await drawer.getByRole('button', { name: 'Tutup' }).click()
    await expect(drawer).toBeHidden()

    await fillDisposition(page, {
      action: 'Tolak sinyal',
      reason: 'Tindak lanjut yang sah, bukan tagihan berulang',
      note: 'Rentang kunjungan kedua klaim tidak bertumpang tindih.',
    })
    await page.getByRole('button', { name: 'Simpan disposisi' }).click()
    await expect(page).toHaveURL(/localhost:\d+\/$/)

    await page.goto(`/cases/${target.case_id}`)
    await page.getByRole('tab', { name: 'Riwayat audit' }).click()
    await expect(page.getByRole('region', { name: 'Riwayat audit' })).toContainText(
      'Tolak sinyal',
    )
  })
})

test.describe('error path — a stale version is refused without losing input', () => {
  /**
   * `brief/04_DETAIL_KASUS_DISPOSISI.md` § 4.3 treats overwriting a colleague's decision as an
   * accountability failure rather than a concurrency bug — and treats losing the reviewer's
   * work on the way to refusing it as a second failure on top of the first.
   */
  test('the banner names what changed and who changed it, and the draft survives', async ({
    page,
    request,
  }) => {
    const target = await findOpenCase(request, 'UNBUNDLING_FRAGMENTATION')
    await page.goto(`/cases/${target.case_id}`)

    const note = 'Catatan ini tidak boleh hilang ketika penyimpanan ditolak.'
    await fillDisposition(page, {
      action: 'Eskalasi',
      reason: 'Perlu penelusuran oleh unit berwenang',
      note,
    })

    // Somebody else moves the case while this reviewer is still reading it.
    await dispositionAsAnotherReviewer(request, target.case_id, target.case_version)

    await page.getByRole('button', { name: 'Simpan disposisi' }).click()

    const banner = page.getByRole('alert')
    await expect(banner).toContainText('Versi kasus tidak cocok')
    await expect(banner).toContainText('Peninjau senior')
    await expect(banner).toContainText('Menunggu bukti')
    await expect(banner).toContainText('Isian disposisi Anda tetap dipertahankan')
    await expect(banner.getByRole('button', { name: 'Muat ulang' })).toBeVisible()

    // The input is still there, exactly as typed.
    await expect(page.getByRole('radio', { name: /Eskalasi/ })).toBeChecked()
    await expect(page.getByLabel('ALASAN TERSTRUKTUR')).toHaveValue(
      'Perlu penelusuran oleh unit berwenang',
    )
    await expect(page.getByLabel('CATATAN BEBAS')).toHaveValue(note)

    // And nothing was written: the reviewer's action is absent from the history.
    await page.getByRole('tab', { name: 'Riwayat audit' }).click()
    await expect(page.getByRole('region', { name: 'Riwayat audit' })).not.toContainText(
      'Perlu penelusuran oleh unit berwenang',
    )
  })
})

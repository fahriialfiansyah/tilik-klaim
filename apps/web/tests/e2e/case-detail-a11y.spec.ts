import { expect, test } from '@playwright/test'

import { findOpenCase } from './helpers'

/**
 * Accessibility smoke for the case-detail flow.
 *
 * `sprint/00-app-spec.md` § 4 rule 5 and `brief/04_DETAIL_KASUS_DISPOSISI.md` § 9.4 make two
 * promises this covers: the whole flow completes from the keyboard, and closing the comparison
 * drawer returns focus somewhere sensible. Both are the kind of thing that works on the day it
 * is built and quietly stops working three components later.
 */

test('the disposition flow completes without a mouse', async ({ page, request }) => {
  const target = await findOpenCase(request, 'PHANTOM_OR_NO_PROCEDURE_EVIDENCE')
  await page.goto(`/cases/${target.case_id}`)

  // Reach the action group by keyboard alone and choose with the keyboard.
  const firstAction = page.getByRole('radio', { name: /Tolak sinyal/ })
  await firstAction.focus()
  await page.keyboard.press('Space')
  await expect(firstAction).toBeChecked()

  // Arrow keys move within the radio group, as a radio group must.
  await page.keyboard.press('ArrowDown')
  await expect(page.getByRole('radio', { name: /Minta bukti tambahan/ })).toBeChecked()

  await page.getByLabel('ALASAN TERSTRUKTUR').focus()
  await page.getByLabel('ALASAN TERSTRUKTUR').selectOption('Berkas pendukung belum lengkap')
  await page.getByLabel('CATATAN BEBAS').focus()
  await page.keyboard.type('Diisi lewat papan ketik.')

  await expect(page.getByRole('button', { name: 'Simpan disposisi' })).toBeEnabled()
})

test('a drawer traps focus, closes on Escape, and hands focus back to its trigger', async ({
  page,
  request,
}) => {
  const target = await findOpenCase(request, 'CLONED_DOCUMENTATION')
  await page.goto(`/cases/${target.case_id}`)

  const trigger = page.getByRole('button', { name: 'Bandingkan pasangan kandidat' })
  await trigger.focus()
  await page.keyboard.press('Enter')

  const drawer = page.getByRole('dialog')
  await expect(drawer).toBeVisible()
  // Focus moved into the drawer rather than staying behind it.
  await expect(drawer).toContainText('Perbandingan pasangan kandidat')
  const focusedInsideDrawer = await page.evaluate(() => {
    const dialog = document.querySelector('[role="dialog"]')
    return Boolean(dialog && document.activeElement && dialog.contains(document.activeElement))
  })
  expect(focusedInsideDrawer).toBe(true)

  await page.keyboard.press('Escape')
  await expect(drawer).toBeHidden()
  await expect(trigger).toBeFocused()
})

test('every evidence reference is reachable and states what it is', async ({ page, request }) => {
  const target = await findOpenCase(request, 'PHANTOM_OR_NO_PROCEDURE_EVIDENCE')
  await page.goto(`/cases/${target.case_id}`)

  // Display rule 4: an unopenable reference is a defect, so the seeded fixtures must show none.
  await expect(page.getByTestId('evidence-ref-broken')).toHaveCount(0)

  const reference = page.getByRole('button', { name: /Kunjungan ENC-/ }).first()
  await reference.focus()
  await page.keyboard.press('Enter')

  const panel = page.getByRole('dialog')
  await expect(panel).toBeVisible()
  await expect(panel).toContainText('Ada di bundel ini')
  await expect(panel).toContainText('VERSI MESIN SAAT KASUS DISARING')

  await page.keyboard.press('Escape')
  await expect(panel).toBeHidden()
  await expect(reference).toBeFocused()
})

test('the band is never conveyed by colour alone', async ({ page, request }) => {
  const target = await findOpenCase(request, 'PHANTOM_OR_NO_PROCEDURE_EVIDENCE')
  await page.goto(`/cases/${target.case_id}`)

  const header = page.getByRole('region', { name: 'Kepala kasus' })
  await expect(header).toContainText('Konflik deterministik')
  // And the support state of a billed line carries its words too.
  await expect(page.getByRole('region', { name: 'Daftar baris tagihan' })).toContainText(
    'Tidak didukung',
  )
})

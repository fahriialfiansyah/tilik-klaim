import { execFileSync } from 'node:child_process'
import path from 'node:path'

import { expect, test } from '@playwright/test'

import { findOpenCase } from './helpers'

/**
 * The Evidence Workspace (ADR-0004) against the real API and a seeded database.
 *
 * Two promises are the ones most likely to quietly break: the matrix and the swimlane *draw the
 * phantom finding* rather than narrate it, and a reviewer can get from a matrix cell into a
 * drawer and back to the same cell without a mouse (display rule 5).
 *
 * **Resets first, like `demo-flow.spec.ts`.** Specs that sort earlier disposition the only
 * phantom case, and these tests read that case. Nothing here mutates, so the reset leaves the
 * database in the state the remaining specs expect.
 */

test.beforeAll(() => {
  execFileSync('uv', ['run', 'python', 'scripts/demo_reset.py'], {
    cwd: path.resolve(process.cwd(), '../backend'),
    stdio: 'pipe',
  })
})

test('the phantom finding is drawn: a MISSING cell and a gap in the procedure lane', async ({
  page,
  request,
}) => {
  const target = await findOpenCase(request, 'PHANTOM_OR_NO_PROCEDURE_EVIDENCE')
  await page.goto(`/cases/${target.case_id}`)

  const matrix = page.getByRole('table', { name: 'Matriks bukti' })
  await expect(matrix).toBeVisible()
  await expect(matrix).toContainText('tidak ditemukan')
  // The untouched line's cells say nobody expected anything there — the fourth state.
  await expect(matrix).toContainText('tidak diharapkan')

  // The seeded case has a completed procedure for 89.7 and none for 88.71. So the *Tindakan*
  // lane is not empty — it has a gap in the column where 88.71 was billed. The billing lane
  // names both lines; the procedure lane names only the first. That gap is the finding.
  const lanes = page.getByRole('table', { name: 'Linimasa episode' })
  await expect(lanes.getByRole('row', { name: /Penagihan/ })).toContainText('88.71')
  await expect(lanes.getByRole('row', { name: /Tindakan/ })).toContainText('89.7')
  await expect(lanes.getByRole('row', { name: /Tindakan/ })).not.toContainText('88.71')
})

test('the map is anchored on the open reason and terminates in words', async ({ page, request }) => {
  const target = await findOpenCase(request, 'PHANTOM_OR_NO_PROCEDURE_EVIDENCE')
  await page.goto(`/cases/${target.case_id}`)

  const map = page.getByRole('region', { name: 'Peta bukti' })
  await expect(map).toContainText('tidak punya catatan tindakan yang selesai')
  const terminals = map.getByRole('list', { name: 'Bukti yang diharapkan' })
  await expect(terminals).toContainText('Tindakan')
  await expect(terminals).toContainText('tidak ditemukan')
  // Counter-evidence is drawn on its own branch, labelled, in addition to the reason card.
  await expect(map.getByRole('list', { name: 'Bukti tandingan' })).toContainText(/hanya memuat bukti/)
})

test('keyboard: a matrix cell opens the source drawer and gets focus back on Escape', async ({
  page,
  request,
}) => {
  const target = await findOpenCase(request, 'PHANTOM_OR_NO_PROCEDURE_EVIDENCE')
  await page.goto(`/cases/${target.case_id}`)

  const matrix = page.getByRole('table', { name: 'Matriks bukti' })
  const cellRef = matrix.getByRole('button', { name: /Kunjungan ENC-/ }).first()
  await cellRef.focus()
  await page.keyboard.press('Enter')

  const drawer = page.getByRole('dialog')
  await expect(drawer).toBeVisible()
  await expect(drawer).toContainText('Ada di bundel ini')

  await page.keyboard.press('Escape')
  await expect(drawer).toBeHidden()
  await expect(cellRef).toBeFocused()
})

test('one drawer at a time: opening a comparison after a source leaves a single dialog', async ({
  page,
  request,
}) => {
  const target = await findOpenCase(request, 'CLONED_DOCUMENTATION')
  await page.goto(`/cases/${target.case_id}`)

  await page.getByRole('button', { name: /Kunjungan ENC-/ }).first().click()
  await expect(page.getByRole('dialog')).toBeVisible()
  await page.keyboard.press('Escape')
  await expect(page.getByRole('dialog')).toBeHidden()

  await page.getByRole('button', { name: 'Bandingkan pasangan kandidat' }).click()
  // Strict-mode locator: two dialogs would fail this line.
  await expect(page.getByRole('dialog')).toContainText('Perbandingan pasangan kandidat')
})

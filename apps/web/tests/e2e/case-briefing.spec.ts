import { execFileSync } from 'node:child_process'
import path from 'node:path'

import { expect, test } from '@playwright/test'

import { findOpenCase } from './helpers'

/**
 * The bounded, read-only Case Briefing (ADR-0005) against the real API with the LLM **off** —
 * which is the default, and the configuration the offline demo runs. What is asserted is the
 * template path end to end, through the dev proxy, streamed.
 */

test.beforeAll(() => {
  execFileSync('uv', ['run', 'python', 'scripts/demo_reset.py'], {
    cwd: path.resolve(process.cwd(), '../backend'),
    stdio: 'pipe',
  })
})

test('the panel is collapsed, last in the column, and volunteers nothing', async ({ page, request }) => {
  const target = await findOpenCase(request, 'PHANTOM_OR_NO_PROCEDURE_EVIDENCE')
  const briefingRequests: string[] = []
  page.on('request', (req) => {
    if (req.url().includes('/briefing')) {
      briefingRequests.push(req.url())
    }
  })
  await page.goto(`/cases/${target.case_id}`)
  await page.getByRole('table', { name: 'Matriks bukti' }).waitFor()

  const toggle = page.getByRole('button', { name: /Ringkasan bukti/ })
  await expect(toggle).toHaveAttribute('aria-expanded', 'false')
  expect(briefingRequests).toEqual([])

  // Reason before summary: the panel sits below the swimlane in DOM order.
  const order = await page.evaluate(() => {
    const lanes = document.querySelector('[aria-label="Linimasa episode"]')
    const panel = document.querySelector('[aria-label="Ringkasan bukti"]')
    return lanes && panel ? lanes.compareDocumentPosition(panel) & Node.DOCUMENT_POSITION_FOLLOWING : 0
  })
  expect(order).toBeTruthy()
})

test('asking for a briefing streams the template, with provenance and openable references', async ({
  page,
  request,
}) => {
  const target = await findOpenCase(request, 'PHANTOM_OR_NO_PROCEDURE_EVIDENCE')
  await page.goto(`/cases/${target.case_id}`)
  await page.getByRole('button', { name: /Ringkasan bukti/ }).click()
  await page.getByRole('button', { name: 'Susun ringkasan' }).click()

  const panel = page.getByRole('region', { name: 'Ringkasan bukti' })
  await expect(panel).toContainText('PENGAMATAN')
  await expect(panel).toContainText('Templat deterministik')
  await expect(panel).toContainText('KETIDAKPASTIAN')
  // The template reads the catalog sentence; nothing here says fraud.
  await expect(panel).toContainText('tidak punya catatan tindakan')
  await expect(panel).not.toContainText(/fraud/i)
  // Not the fallback path: the stream itself delivered it through the dev proxy.
  await expect(panel).not.toContainText('dimuat tanpa aliran')

  // A cited reference opens the same drawer as everywhere else, and Escape returns focus.
  const ref = panel.getByRole('button', { name: /Kunjungan ENC-/ }).first()
  await ref.focus()
  await page.keyboard.press('Enter')
  await expect(page.getByRole('dialog')).toContainText('Ada di bundel ini')
  await page.keyboard.press('Escape')
  await expect(ref).toBeFocused()
})

test('the briefing never touches the disposition draft', async ({ page, request }) => {
  const target = await findOpenCase(request, 'PHANTOM_OR_NO_PROCEDURE_EVIDENCE')
  await page.goto(`/cases/${target.case_id}`)
  await page.getByRole('radio', { name: /Eskalasi/ }).click()
  await page.getByLabel('CATATAN BEBAS').fill('Setengah jalan.')

  await page.getByRole('button', { name: /Ringkasan bukti/ }).click()
  await page.getByRole('button', { name: 'Susun ringkasan' }).click()
  await expect(page.getByRole('region', { name: 'Ringkasan bukti' })).toContainText('PENGAMATAN')

  await expect(page.getByRole('radio', { name: /Eskalasi/ })).toBeChecked()
  await expect(page.getByLabel('CATATAN BEBAS')).toHaveValue('Setengah jalan.')
  await expect(page.getByLabel('ALASAN TERSTRUKTUR')).toHaveValue('')
})

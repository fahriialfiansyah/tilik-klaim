import { execFileSync } from 'node:child_process'
import path from 'node:path'

import { expect, test } from '@playwright/test'

import { findOpenCase, signInAs } from './helpers'

/**
 * Every spec below runs as a signed-in reviewer.
 *
 * The session is seeded into `localStorage` rather than typed into the login form: these specs
 * are about the review flow, and walking three extra clicks at the top of each would test the
 * same thing twenty times while adding a failure mode to specs that are not about it.
 * `auth-roles.spec.ts` signs in for real, so the form itself stays covered.
 */
test.beforeEach(async ({ page }) => {
  await signInAs(page)
})

/**
 * The bounded, read-only Case Briefing (ADR-0005) against the real API, through the dev proxy,
 * streamed.
 *
 * **Provenance is asserted as "one of the two", not as the template.** Whether a model answers
 * is the developer's own `.env`, and a spec that pinned the template would fail on a machine
 * where the gateway is configured — reporting a working feature as broken. What must hold on
 * both paths is what the guarantees actually are: the panel says how it was produced, every
 * observation carries an openable reference, and nothing accusatory appears.
 *
 * The briefing assertions carry their own timeout. A real gateway call takes tens of seconds —
 * the suite's 7-second default is right for a rendered page and wrong for a model, and the
 * failure it produces looks like a broken panel rather than a slow one.
 */

/** Long enough for a real gateway round trip; the template path answers instantly. */
const BRIEFING_TIMEOUT = 180_000

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
  await expect(panel).toContainText('PENGAMATAN', { timeout: BRIEFING_TIMEOUT })
  await expect(panel).toContainText('KETIDAKPASTIAN')
  // Always states how it was produced, whichever path answered.
  await expect(panel).toContainText(/Templat deterministik|Model bahasa, tervalidasi/)
  await expect(panel).not.toContainText(/fraud|curang|pemalsuan|sanksi/i)
  // Every observation is source-bound, so at least one openable reference is on screen.
  expect(await panel.getByRole('button', { name: /ENC-|LN-|CLM-|DOC-|PROC-/ }).count()).toBeGreaterThan(0)
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
  await expect(page.getByRole('region', { name: 'Ringkasan bukti' })).toContainText(
    'PENGAMATAN',
    { timeout: BRIEFING_TIMEOUT },
  )

  await expect(page.getByRole('radio', { name: /Eskalasi/ })).toBeChecked()
  await expect(page.getByLabel('CATATAN BEBAS')).toHaveValue('Setengah jalan.')
  await expect(page.getByLabel('ALASAN TERSTRUKTUR')).toHaveValue('')
})

import { expect, test } from '@playwright/test'

import { signInAs } from './helpers'

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
 * The ingest screen, against the real API.
 *
 * The point of this page is that the system works **from input**, so mocking the ingest and
 * screen calls would test everything except the claim it makes. These specs submit real bundles
 * and follow the case they produce.
 */

const report = (page: import('@playwright/test').Page) =>
  page.getByRole('region', { name: 'Laporan validasi' })

test('a seeded scenario screens through to its case detail', async ({ page }) => {
  await page.goto('/ingest')

  // The limits are readable before anything is uploaded, not after a failure.
  await expect(page.getByText('Ukuran maksimum')).toBeVisible()
  await expect(page.getByText('8 MB')).toBeVisible()

  await expect(report(page)).toContainText('Belum ada berkas')

  await page.getByRole('button', { name: /Tagihan tanpa bukti tindakan/ }).click()

  await expect(report(page)).toContainText('Sah')
  await expect(report(page)).toContainText('Baris tagihan')
  await expect(report(page)).toContainText('sha256:')

  // Exactly one action. A configuration wizard on this screen would let a presenter tune their
  // way to a result, which is why `sprint/00-app-spec.md` § 5 forbids one outright.
  await expect(page.getByRole('combobox')).toHaveCount(0)
  await expect(report(page)).toContainText('Tidak ada langkah konfigurasi')

  await page.getByRole('button', { name: 'Saring klaim' }).click()

  await expect(page).toHaveURL(/\/cases\/case_/)
  await expect(page.getByRole('heading', { level: 1 })).toContainText(
    'tidak punya catatan tindakan yang selesai',
  )
})

test('a scenario that needs a prior claim says so, and its cross-claim reason fires', async ({
  page,
}) => {
  await page.goto('/ingest')

  const repeat = page.getByRole('button', { name: /Tagihan berulang/ })
  await expect(repeat).toContainText('1 klaim riwayat')
  await repeat.click()

  await expect(report(page)).toContainText('Sah')
  await page.getByRole('button', { name: 'Saring klaim' }).click()

  await expect(page).toHaveURL(/\/cases\/case_/)
  await expect(page.getByRole('heading', { level: 1 })).toContainText('bertumpang tindih')
})

test('resubmitting an identical bundle points at the existing case instead of making a second', async ({
  page,
}) => {
  await page.goto('/ingest')
  await page.getByRole('button', { name: /Episode terpecah/ }).click()
  await expect(report(page)).toContainText('Sah')
  await page.getByRole('button', { name: 'Saring klaim' }).click()
  await expect(page).toHaveURL(/\/cases\/case_/)
  const caseUrl = page.url()

  await page.goto('/ingest')
  await page.getByRole('button', { name: /Episode terpecah/ }).click()

  const notice = page.getByText('Bundel dengan sidik digital identik pernah disaring')
  await expect(notice).toBeVisible()
  await page.getByRole('button', { name: 'Buka kasus' }).click()
  await expect(page).toHaveURL(caseUrl)
})

test('an invalid bundle disables the screen button and names the resource at fault', async ({
  page,
}) => {
  await page.goto('/ingest')

  // A dangling reference: structurally parseable, but pointing at a resource that was never
  // sent. The API accepts the request and reports INVALID, which is a different path from a
  // file it refuses before parsing.
  await page.evaluate(async () => {
    const sample = await (await fetch('/samples/clean.json')).json()
    const bundle = JSON.parse(JSON.stringify(sample.bundle))
    bundle.bundle_id = 'BND-E2E-DANGLING'
    bundle.claim.claim_id = 'CLM-E2E-DANGLING'
    for (const line of bundle.lines) {
      line.claim_id = 'CLM-E2E-DANGLING'
    }
    bundle.lines[0].supporting_refs = [
      { resource_type: 'Procedure', resource_id: 'PROC-TIDAK-ADA' },
    ]
    const input = document.querySelector('input[type=file]') as HTMLInputElement
    const transfer = new DataTransfer()
    transfer.items.add(
      new File([JSON.stringify(bundle)], 'menggantung.json', { type: 'application/json' }),
    )
    input.files = transfer.files
    input.dispatchEvent(new Event('change', { bubbles: true }))
  })

  await expect(report(page)).toContainText('Tidak sah')
  await expect(page.getByRole('button', { name: 'Saring klaim' })).toBeDisabled()
  await expect(report(page)).toContainText('tidak ada penyaringan sebagian')

  const issues = page.getByRole('region', { name: 'Galat dan peringatan' })
  await expect(issues).toContainText('BUNDLE_DANGLING_REFERENCE')
  await expect(issues).toContainText('PROC-TIDAK-ADA')
  await expect(issues).toContainText('cacat integritas bukti')
})

test('an oversized file is refused in the browser, before anything is sent', async ({ page }) => {
  await page.goto('/ingest')

  const sent = await page.evaluate(async () => {
    const before = performance.now()
    const input = document.querySelector('input[type=file]') as HTMLInputElement
    const transfer = new DataTransfer()
    transfer.items.add(
      new File([new Uint8Array(9 * 1024 * 1024)], 'besar.json', { type: 'application/json' }),
    )
    input.files = transfer.files
    input.dispatchEvent(new Event('change', { bubbles: true }))
    await new Promise((resolve) => setTimeout(resolve, 400))
    return performance
      .getEntriesByType('resource')
      .filter((entry) => entry.name.includes('/v1/bundles') && entry.startTime > before).length
  })

  expect(sent, 'the file must not leave the browser').toBe(0)
  await expect(page.getByRole('alert')).toContainText('melampaui batas 8 MB')
  await expect(page.getByRole('button', { name: 'Saring klaim' })).toBeDisabled()
})

test('an incomplete but well-formed bundle screens, and says why its notes matter', async ({
  page,
}) => {
  await page.goto('/ingest')

  await page.evaluate(async () => {
    const sample = await (await fetch('/samples/clean.json')).json()
    const bundle = JSON.parse(JSON.stringify(sample.bundle))
    bundle.bundle_id = 'BND-E2E-THIN'
    bundle.claim.claim_id = 'CLM-E2E-THIN'
    bundle.procedures = []
    bundle.medications = []
    bundle.charge_items = []
    bundle.invoices = []
    bundle.provenance = []
    for (const line of bundle.lines) {
      line.claim_id = 'CLM-E2E-THIN'
      line.supporting_refs = []
      line.charge_item_ref = null
    }
    const input = document.querySelector('input[type=file]') as HTMLInputElement
    const transfer = new DataTransfer()
    transfer.items.add(
      new File([JSON.stringify(bundle)], 'tipis.json', { type: 'application/json' }),
    )
    input.files = transfer.files
    input.dispatchEvent(new Event('change', { bubbles: true }))
  })

  await expect(report(page)).toContainText('Sah dengan catatan')

  // The distinction the whole module exists to protect: a thin record lowers certainty and
  // points at requesting documents. It never raises a risk signal.
  const notes = page.getByRole('note').filter({ hasText: 'Catatan kelengkapan berkas' })
  await expect(notes).toContainText('minta bukti tambahan')
  await expect(notes).toContainText('bukan')

  // And it still screens — a thin record is not a rejected one.
  await expect(page.getByRole('button', { name: 'Saring klaim' })).toBeEnabled()
})

test('arriving from a case carries that case with it', async ({ page }) => {
  await page.goto('/ingest?case=case_contoh')

  const banner = page.getByRole('note').filter({ hasText: 'permintaan bukti tambahan' })
  await expect(banner).toBeVisible()
  await banner.getByRole('button', { name: 'Buka kasus' }).click()
  await expect(page).toHaveURL(/\/cases\/case_contoh/)
})

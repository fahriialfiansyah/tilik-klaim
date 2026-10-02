import { execFileSync } from 'node:child_process'
import path from 'node:path'

import { expect, test, type Page } from '@playwright/test'

import { findOpenCase, signInAs } from './helpers'

/**
 * Asisten Bukti (ADR-0007) against the real API, through the dev proxy, streamed.
 *
 * **Provenance is asserted as "one of the two"**, as in the briefing spec: whether a model answers
 * is the developer's own `.env` (`ASSISTANT_ENABLED`), and a spec that pinned the template would
 * report a working feature as broken on a machine where the gateway is switched on. What must
 * hold on both paths is what ADR-0007 guarantees: every statement is cited, every citation opens,
 * nothing accusatory is said, and a refused question is refused before any model is asked.
 */
const ANSWER_TIMEOUT = 180_000

const FORBIDDEN = /fraud|curang|kecurangan|pemalsuan|palsu|sanksi|\bterbukti\b|\bbersih\b/i

/**
 * Whether this API answers from the deterministic template. A handful of assertions below pin
 * the template's exact shape — which case card comes first, which citation kinds a comparison
 * carries — and are skipped, saying so, when a model is answering instead; the model path has
 * its own spec, `assistant-model.spec.ts`, asserting only what holds on both.
 */
async function onTemplatePath(request: import('@playwright/test').APIRequestContext): Promise<boolean> {
  const response = await request.post('/v1/assistant/answers?stream=false', {
    headers: { 'X-Actor-Role': 'reviewer' },
    data: { question: 'Ringkas kondisi antrean' },
  })
  const body = await response.json()
  return body.generated_by === 'TEMPLATE' && body.validation_rejected === false
}

test.beforeAll(() => {
  execFileSync('uv', ['run', 'python', 'scripts/demo_reset.py'], {
    cwd: path.resolve(process.cwd(), '../backend'),
    stdio: 'pipe',
  })
})

test.beforeEach(async ({ page }) => {
  await signInAs(page)
})

const composer = (page: Page) => page.getByRole('textbox', { name: 'Pertanyaan untuk Asisten Bukti' })
const thread = (page: Page) => page.getByRole('log', { name: 'Percakapan dengan Asisten Bukti' })
const latestTurn = (page: Page) => thread(page).getByRole('article').last()

async function ask(page: Page, question: string): Promise<void> {
  await composer(page).fill(question)
  await composer(page).press('Enter')
  await expect(latestTurn(page)).toContainText(/CARA DISUSUN|Di luar cakupan|belum dikenali/, {
    timeout: ANSWER_TIMEOUT,
  })
}

test.describe('the page and its entry', () => {
  test('the sidebar reaches it and the page says what it reads before anything is asked', async ({
    page,
  }) => {
    await page.goto('/')
    await page.getByRole('navigation').getByRole('link', { name: 'Asisten Bukti' }).click()

    await expect(page).toHaveURL(/\/assistant$/)
    await expect(page.getByRole('heading', { level: 1, name: 'Asisten Bukti' })).toBeVisible()
    await expect(page).toHaveTitle('Asisten Bukti · TilikKlaim')
    await expect(page.getByRole('heading', { name: 'Apa yang ingin Anda telusuri?' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Kasus mana yang perlu dibuka dulu?' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Ubah cakupan: Seluruh antrean' })).toBeVisible()

    // The limits are on the page, not only in the ADR.
    const context = page.getByRole('complementary', { name: 'Konteks Asisten Bukti' })
    await expect(context).toContainText('Tidak menilai niat atau kesalahan siapa pun')
    await expect(context).toContainText('Tidak mengubah prioritas, status, atau keputusan')
    // No "AI" anywhere on the page, in either sense of the word's use here.
    await expect(page.locator('main')).not.toContainText(/\bAI\b/)
  })
})

test.describe('answers are cited, and every citation opens', () => {
  test('"where to start" points at the queue\'s own top case, streamed', async ({ page, request }) => {
    test.skip(!(await onTemplatePath(request)), 'pins the template answer; see assistant-model.spec.ts')
    const queue = (await (await request.get('/v1/cases?page_size=50')).json()).items as {
      case_id: string
      state: string
    }[]
    const top = queue.find((row) => ['SCREENED', 'IN_REVIEW'].includes(row.state))
    expect(top, 'the seed must leave a case awaiting review').toBeTruthy()

    await page.goto('/assistant')
    await page.getByRole('button', { name: 'Kasus mana yang perlu dibuka dulu?' }).click()
    const turn = latestTurn(page)
    await expect(turn).toContainText('CARA DISUSUN', { timeout: ANSWER_TIMEOUT })

    await expect(turn).toContainText(/Templat deterministik|Model bahasa, tervalidasi/)
    await expect(turn).not.toContainText(FORBIDDEN)
    // Delivered by the stream itself through the dev proxy, not by the one-shot fallback.
    await expect(turn).not.toContainText('dimuat tanpa streaming')

    const sources = turn.getByRole('list', { name: 'Sumber' })
    expect(await sources.getByRole('listitem').count()).toBeGreaterThan(0)
    // The first case card is the queue's first awaiting case — the assistant never re-ranks.
    await expect(
      turn.getByRole('link', { name: /Buka kasus/ }).first(),
    ).toHaveAttribute('href', `/cases/${top?.case_id}`)
  })

  test('a cited resource opens the source drawer, and Escape returns focus to the citation', async ({
    page,
    request,
  }) => {
    test.skip(!(await onTemplatePath(request)), 'pins the template answer; see assistant-model.spec.ts')
    const target = await findOpenCase(request, 'PHANTOM_OR_NO_PROCEDURE_EVIDENCE')
    await page.goto(`/assistant?case=${target.case_id}`)
    await expect(page.getByRole('button', { name: /^Ubah cakupan: Kasus case_/ })).toBeVisible()

    await ask(page, 'Bukti apa yang belum ditemukan?')
    const turn = latestTurn(page)
    await expect(turn).not.toContainText(FORBIDDEN)

    const citation = turn.getByRole('button', { name: /^Sumber \d+: (baris tagihan|kunjungan|catatan tindakan)/ }).first()
    await citation.focus()
    await page.keyboard.press('Enter')
    await expect(page.getByRole('dialog')).toContainText('Ada di bundel ini')
    await page.keyboard.press('Escape')
    await expect(page.getByRole('dialog')).toBeHidden()
    await expect(citation).toBeFocused()
  })

  test('a case card narrows the scope, and a cited case opens its detail and back', async ({
    page,
    request,
  }) => {
    test.skip(!(await onTemplatePath(request)), 'pins the template answer; see assistant-model.spec.ts')
    await page.goto('/assistant')
    await ask(page, 'Kasus apa saja dengan tagihan berulang?')

    const turn = latestTurn(page)
    await turn.getByRole('button', { name: /^Persempit cakupan ke kasus/ }).first().click()
    await expect(page).toHaveURL(/\/assistant\?case=case_/)
    await expect(page.getByRole('button', { name: /^Ubah cakupan: Kasus case_/ })).toBeVisible()

    // A repeat-billing pair is cited by its two claims and the overlapping line, all openable.
    await ask(page, 'Dengan apa kasus ini dibandingkan?')
    await expect(latestTurn(page)).toContainText(/Dibandingkan dengan|pembanding/i)
    await expect(latestTurn(page).getByRole('button', { name: /^Sumber \d+: klaim / }).first()).toBeVisible()

    // "Why" cites the case itself — a real link; the conversation survives the round trip.
    await ask(page, 'Mengapa kasus ini muncul?')
    await latestTurn(page).getByRole('link', { name: /^Sumber \d+: Kasus case_/ }).first().click()
    await expect(page).toHaveURL(/\/cases\/case_/)
    await page.goBack()
    await expect(thread(page).getByRole('article')).toHaveCount(3)
  })
})

test.describe('what it refuses, and how it says so', () => {
  test('a verdict question is refused in plain words and offers what it can do instead', async ({
    page,
  }) => {
    await page.goto('/assistant')
    await ask(page, 'Apakah rumah sakit ini curang?')

    const turn = latestTurn(page)
    await expect(turn).toContainText('Di luar cakupan asisten')
    await expect(turn).toContainText('melaporkan risiko atau anomali yang perlu ditinjau')
    await expect(turn.getByRole('list', { name: 'Sumber' })).toHaveCount(0)
    // A refusal never reads anything: no model, no tool.
    await expect(turn).toContainText('tanpa langkah membaca')

    // The offered question is answered — by the template or a model; either way it says how.
    await turn.getByRole('button', { name: /Ringkas kondisi antrean/ }).click()
    await expect(thread(page).getByRole('article')).toHaveCount(2)
    await expect(latestTurn(page)).toContainText('CARA DISUSUN', { timeout: ANSWER_TIMEOUT })
  })

  test('the API refuses the same question before any model, and refuses an administrator', async ({
    request,
  }) => {
    const refused = await request.post('/v1/assistant/answers?stream=false', {
      headers: { 'X-Actor-Role': 'reviewer' },
      data: { question: 'Should we reject this claim?' },
    })
    const body = await refused.json()
    expect(body.kind).toBe('REFUSAL')
    expect(body.refusal_topic).toBe('DECISION')
    expect(body.tool_calls).toEqual([])

    const admin = await request.post('/v1/assistant/answers?stream=false', {
      headers: { 'X-Actor-Role': 'admin' },
      data: { question: 'Ringkas antrean' },
    })
    expect(admin.status()).toBe(403)
    expect((await admin.json()).code).toBe('CASE_ACCESS_FORBIDDEN')
  })
})

test.describe('roles and language', () => {
  test('an administrator has no entry and is turned away from the route', async ({ browser }) => {
    const context = await browser.newContext()
    const page = await context.newPage()
    await signInAs(page, 'admin')
    await page.goto('/assistant')
    await expect(page).toHaveURL(/\/admin\/users$/)
    await expect(page.getByRole('navigation').getByRole('link', { name: 'Asisten Bukti' })).toHaveCount(0)
    await context.close()
  })

  test('in English the page and the answer are English', async ({ page }) => {
    await page.addInitScript(() => window.localStorage.setItem('tilik-locale', 'en'))
    await page.goto('/assistant')
    await expect(page.getByRole('heading', { level: 1, name: 'Evidence Assistant' })).toBeVisible()

    const input = page.getByRole('textbox', { name: 'Question for the Evidence Assistant' })
    await input.fill('Which cases show repeat billing?')
    await input.press('Enter')
    const turn = page
      .getByRole('log', { name: 'Conversation with the Evidence Assistant' })
      .getByRole('article')
      .last()
    await expect(turn).toContainText('HOW THIS WAS MADE', { timeout: ANSWER_TIMEOUT })
    await expect(turn).toContainText(/Repeat billing|repeat billing|overlapping/i)
    await expect(turn).not.toContainText(/fraud|falsif|sanction/i)
  })
})

test.describe('the input and the turn lifecycle', () => {
  test('Shift+Enter breaks the line, Enter sends, and the scope picker switches to one case', async ({
    page,
  }) => {
    await page.goto('/assistant')
    await composer(page).click()
    await page.keyboard.type('baris satu')
    await page.keyboard.press('Shift+Enter')
    await page.keyboard.type('baris dua')
    await expect(composer(page)).toHaveValue('baris satu\nbaris dua')

    await page.getByRole('button', { name: 'Ubah cakupan: Seluruh antrean' }).click()
    await page.getByRole('menu').getByRole('menuitem').nth(1).click()
    await expect(page).toHaveURL(/\/assistant\?case=case_/)
    await expect(page.getByText(/^TENTANG KASUS case_/)).toBeVisible()
  })

  test('a question over the limit is stopped at the input', async ({ page }) => {
    await page.goto('/assistant')
    await composer(page).fill('x'.repeat(501))
    await expect(page.getByText(/Pertanyaan terlalu panjang/)).toBeVisible()
    await expect(page.getByRole('button', { name: 'Kirim pertanyaan' })).toBeDisabled()
  })

  test('an unreachable service is said in words, and "try again" recovers', async ({ page }) => {
    await page.route('**/v1/assistant/answers**', (route) => route.abort('failed'))
    await page.goto('/assistant')
    await composer(page).fill('Ringkas kondisi antrean')
    await composer(page).press('Enter')

    const alert = latestTurn(page).getByRole('alert')
    await expect(alert).toContainText('Layanan tidak merespons')
    await expect(alert.getByText('Detail teknis')).toBeVisible()

    await page.unroute('**/v1/assistant/answers**')
    await alert.getByRole('button', { name: 'Coba lagi' }).click()
    await expect(latestTurn(page)).toContainText('CARA DISUSUN', { timeout: ANSWER_TIMEOUT })
  })

  test('stop ends a turn that is still being prepared', async ({ page }) => {
    await page.route('**/v1/assistant/answers**', async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 5_000))
      await route.continue().catch(() => undefined)
    })
    await page.goto('/assistant')
    await composer(page).fill('Ringkas kondisi antrean')
    await composer(page).press('Enter')

    await page.getByRole('button', { name: 'Hentikan' }).click()
    await expect(latestTurn(page)).toContainText('Dihentikan sebelum jawaban selesai disusun.')
    await expect(page.getByRole('button', { name: 'Kirim pertanyaan' })).toBeVisible()
  })

  test('"new conversation" clears the thread', async ({ page }) => {
    await page.goto('/assistant')
    await ask(page, 'Ringkas kondisi antrean')
    await page.getByRole('button', { name: 'Percakapan baru' }).click()
    await expect(thread(page).getByRole('article')).toHaveCount(0)
    await expect(page.getByRole('heading', { name: 'Apa yang ingin Anda telusuri?' })).toBeVisible()
  })
})

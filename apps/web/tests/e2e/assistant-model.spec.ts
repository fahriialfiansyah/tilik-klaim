import { expect, test, type Locator, type Page } from '@playwright/test'

import { findOpenCase, signInAs } from './helpers'

/**
 * Asisten Bukti with a real language model behind it (ADR-0007 § 5, `ASSISTANT_ENABLED=true`).
 *
 * Opt-in, because it needs the gateway: run the API with the switch on and point a web server
 * at it, then `E2E_ASSISTANT_MODEL=1 E2E_BASE_URL=… npx playwright test assistant-model`.
 *
 * Nothing here pins wording — a model's sentences vary run to run. What is asserted is what
 * ADR-0007 guarantees whichever way the answer was made: it says how it was made, every statement
 * carries an openable citation, nothing accusatory and no machine code reaches the reading
 * surface, cards keep the queue's order, and a refused question never reaches the model.
 */
test.skip(!process.env.E2E_ASSISTANT_MODEL, 'needs ASSISTANT_ENABLED=true and a reachable gateway')

const MODEL_TIMEOUT = 150_000
const FORBIDDEN = /fraud|curang|kecurangan|pemalsuan|palsu|sanksi|\bterbukti\b|\bbersih\b|falsif|sanction/i
const MACHINE_CODE = /\b[A-Z]{2,}(?:_[A-Z]+)+\b/

test.beforeEach(async ({ page }) => {
  await signInAs(page)
})

async function ask(page: Page, question: string, inputName = 'Pertanyaan untuk Asisten Bukti'): Promise<Locator> {
  const input = page.getByRole('textbox', { name: inputName })
  await input.fill(question)
  await input.press('Enter')
  const turn = page.getByRole('log').getByRole('article').last()
  await expect(turn).toContainText(/CARA DISUSUN|HOW THIS WAS MADE|Di luar cakupan|belum dikenali|not recognised/, {
    timeout: MODEL_TIMEOUT,
  })
  return turn
}

/** The guarantees that hold on both paths, checked on one rendered answer. */
async function expectBoundAnswer(turn: Locator): Promise<void> {
  await expect(turn).toContainText(/Model bahasa, tervalidasi|Templat deterministik|Language model, validated|Deterministic template/)
  await expect(turn).not.toContainText(FORBIDDEN)

  const statements = turn.locator('p.tk-enter')
  const count = await statements.count()
  for (let index = 0; index < count; index += 1) {
    const statement = statements.nth(index)
    await expect(statement).not.toContainText(MACHINE_CODE)
    // Every statement ends in at least one citation chip — a link or a button named "Sumber n".
    expect(await statement.getByRole('link').count() + (await statement.getByRole('button').count())).toBeGreaterThan(0)
  }

  // Cards, when there are any, are in the queue's own order.
  const positions = (await turn.getByText(/^(Urutan ke-|Position )\d+$/).allTextContents()).map((text) =>
    Number(text.replace(/\D/g, '')),
  )
  expect(positions).toEqual([...positions].sort((a, b) => a - b))
}

test('a free-form queue question is answered, cited, and says how it was made', async ({ page }) => {
  await page.goto('/assistant')
  const turn = await ask(page, 'Apa yang sebaiknya saya periksa lebih dulu di antrean ini, dan mengapa?')
  await expectBoundAnswer(turn)
  // The reading log is there, and it names reads in words, never raw arguments.
  await expect(turn.getByText(/\d+ langkah membaca/)).toBeVisible()
  await expect(turn).not.toContainText(/reason_code=|band=|state=|mode=/)
})

test('a free-form question about one case is answered from that case', async ({ page, request }) => {
  const target = await findOpenCase(request, 'PHANTOM_OR_NO_PROCEDURE_EVIDENCE')
  await page.goto(`/assistant?case=${target.case_id}`)
  const turn = await ask(page, 'Jelaskan dengan bahasa sederhana apa masalah kasus ini')
  await expectBoundAnswer(turn)
  await expect(turn.getByRole('link', { name: /Buka kasus/ }).first()).toHaveAttribute(
    'href',
    `/cases/${target.case_id}`,
  )
})

test('an English question is answered in English', async ({ page }) => {
  await page.addInitScript(() => window.localStorage.setItem('tilik-locale', 'en'))
  await page.goto('/assistant')
  const turn = await ask(page, 'What stands out in the queue today?', 'Question for the Evidence Assistant')
  await expectBoundAnswer(turn)
  await expect(turn).toContainText('HOW THIS WAS MADE')
})

test('a refused question is refused at once, without reading or asking the model', async ({ page }) => {
  await page.goto('/assistant')
  const started = Date.now()
  const turn = await ask(page, 'Apakah fasilitas ini melakukan kecurangan?')
  expect(Date.now() - started).toBeLessThan(10_000)
  await expect(turn).toContainText('Di luar cakupan asisten')
  await expect(turn).toContainText('tanpa langkah membaca')
})

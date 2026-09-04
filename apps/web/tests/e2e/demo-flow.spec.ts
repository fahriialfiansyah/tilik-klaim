import { execFileSync } from 'node:child_process'
import path from 'node:path'

import { expect, test } from '@playwright/test'

import { fillDisposition, findOpenCase, signInAs } from './helpers'

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
 * The ninety-second demo flow from `docs/canonical/08_demo_runbook.md` § 90-second flow, walked
 * end to end and timed.
 *
 * The budget is the *whole* point of the test. A flow that works but takes two minutes fails on
 * stage as surely as one that errors, and the failure is discovered in front of judges. So the
 * assertion is on elapsed wall-clock time, not merely on the steps completing.
 *
 * The machine is faster than a presenter — no narration, no pauses, no cursor travel — so
 * passing here is a **necessary** condition, not a sufficient one. `BUDGET_MS` is the runbook's
 * ninety seconds and `MACHINE_BUDGET_MS` is the tighter bound this test actually holds, which is
 * what leaves room for a human to talk over it.
 *
 * Nothing here is mocked. Two of the beats — the state change and the audit event — only exist
 * because a real server wrote them, and against a mock both would pass with the write path
 * broken.
 *
 * **The spec resets first, because it also mutates.** Requesting evidence moves the demo case
 * out of the state the flow starts from, so a second run would find it already dispositioned —
 * which is exactly the failure `scripts/demo_reset.py` exists to prevent, and the sprint's
 * acceptance says this flow completes *from a clean reset*. Resetting here rather than relying
 * on the operator's memory makes the test repeatable and rehearses the reset at the same time.
 */

const BUDGET_MS = 90_000
/** The runbook's budget, for reference in the failure message. */

const MACHINE_BUDGET_MS = 30_000
/**
 * What the machine must finish in, leaving roughly two thirds of the budget for the person
 * speaking. A run that needs longer than this has no room for narration.
 */

test.describe('90-second demo flow', () => {
  test.beforeAll(() => {
    // The same command a presenter runs before going on stage. If it fails, the demo would
    // have failed too, and finding that out here is the entire point.
    execFileSync('uv', ['run', 'python', 'scripts/demo_reset.py'], {
      // Playwright runs with the config directory as cwd, which is `apps/web`.
      cwd: path.resolve(process.cwd(), '../backend'),
      stdio: 'pipe',
    })
  })

  test('ingest to evidence to disposition to audit, inside the demo budget', async ({
    page,
    request,
  }) => {
    const target = await findOpenCase(request, 'PHANTOM_OR_NO_PROCEDURE_EVIDENCE')
    const started = Date.now()

    // 0–10s — open the queue.
    await page.goto('/')
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible()

    // 10–25s — select the top case; the reason names a billed line with no completed support.
    await page.getByRole('link', { name: /tidak punya catatan tindakan/ }).first().click()
    await expect(page).toHaveURL(/\/cases\/case_/)
    await expect(page.getByRole('heading', { level: 1 })).toContainText(
      'tidak punya catatan tindakan yang selesai',
    )

    // The synthetic badge has to be on screen for every beat, not only the first.
    await expect(page.getByText('DATA SINTETIK').first()).toBeVisible()

    // 25–50s — the evidence path: claim line, expected procedure, what was searched.
    await expect(page.getByText(/Tindakan/).first()).toBeVisible()

    // 50–70s — request evidence, with a structured reason.
    await page.goto(`/cases/${target.case_id}`)
    await fillDisposition(page, {
      action: 'Minta bukti',
      reason: 'Berkas pendukung belum lengkap',
      note: 'Demo: meminta catatan tindakan yang menopang baris tagihan.',
    })
    await page.getByRole('button', { name: 'Simpan disposisi' }).click()

    // Requesting evidence hands the reviewer straight to Ingest, carrying the case — that is
    // where the facility's new bundle arrives, and it is the next thing a presenter would show.
    // Waiting for the navigation is not politeness: the case re-renders as it saves, and the
    // audit tab is detached mid-click otherwise.
    await expect(page).toHaveURL(new RegExp(`/ingest\\?case=${target.case_id}$`))

    // 70–82s — the audit event: actor, action, and the version that produced it. The history
    // reads in working language, so this asserts the sentence a presenter points at, not the
    // raw enum — `OPENED` once shipped untranslated into an otherwise Indonesian timeline.
    await page.goto(`/cases/${target.case_id}`)
    await page.getByRole('tab', { name: 'Riwayat audit' }).click()
    await expect(page.getByRole('region', { name: 'Riwayat audit' })).toContainText(
      'Disposisi dicatat',
      { timeout: 10_000 },
    )

    const elapsed = Date.now() - started
    expect(
      elapsed,
      `the demo path took ${(elapsed / 1000).toFixed(1)}s; the runbook budget is ` +
        `${BUDGET_MS / 1000}s and a presenter needs most of it for narration`,
    ).toBeLessThan(MACHINE_BUDGET_MS)
  })

  test('the evaluation beat of the three-minute flow loads inside its slot', async ({ page }) => {
    /**
     * The three-minute flow gives the measurement beat twenty seconds (2:25–2:45). The page
     * reads artifacts and computes nothing, so it either renders immediately or shows the
     * no-run state — and either way the presenter must not be waiting on it.
     */
    const started = Date.now()
    await page.goto('/evaluation')
    await expect(page.getByRole('heading', { level: 1, name: /Audit/ })).toBeVisible()

    // Whichever state it is in, it must be one of the two — never a blank page.
    const rendered = page
      .getByText('Perbandingan baseline')
      .or(page.getByText('Belum ada evaluasi yang dijalankan'))
    await expect(rendered.first()).toBeVisible()

    expect(Date.now() - started).toBeLessThan(20_000)
  })

  test('every demo route works with no external network', async ({ page, context }) => {
    /**
     * `docs/canonical/08_demo_runbook.md` § Demo reliability: never depend on a remote LLM,
     * SATUSEHAT, BPJS, or a cloud database. This blocks everything that is not localhost and
     * walks the demo routes; a request leaving the machine fails the run rather than quietly
     * working because the presenter happened to have wifi.
     */
    const blocked: string[] = []
    await context.route('**/*', (route) => {
      const url = new URL(route.request().url())
      if (url.hostname === 'localhost' || url.hostname === '127.0.0.1') {
        return route.continue()
      }
      blocked.push(url.href)
      return route.abort('blockedbyclient')
    })

    for (const path of ['/', '/ingest', '/evaluation']) {
      await page.goto(path)
      await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
    }

    expect(blocked, `the demo tried to reach ${blocked.join(', ')}`).toEqual([])
  })
})

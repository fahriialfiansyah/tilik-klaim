import { execFileSync } from 'node:child_process'
import path from 'node:path'

import { expect, test } from '@playwright/test'

import { STAFF, signInAs } from './helpers'

/**
 * Signing in as each of the three roles, and confirming what each one sees and cannot reach.
 *
 * This is the spec that signs in **through the form**, so the real path is covered once rather
 * than twenty times — every other spec seeds the session directly.
 *
 * The refusals are checked at the API as well as in the browser. Hiding a link proves nothing:
 * `apps/backend/tests/test_access.py` owns the exhaustive matrix, and the check here is that the
 * two agree from the outside.
 */
const BACKEND = path.resolve(__dirname, '../../../backend')

/**
 * The page's own `<h1>`, not the audit panel's `<h2>` beneath it.
 *
 * Playwright matches an accessible name by substring, and "Riwayat manajemen pengguna" contains
 * "Manajemen Pengguna" — so an inexact locator resolves to two headings and fails on strict mode.
 */
const ADMIN_HEADING = (page: import('@playwright/test').Page) =>
  page.getByRole('heading', { name: 'Manajemen Pengguna', exact: true })

const LOGIN_HEADING = (page: import('@playwright/test').Page) =>
  page.getByRole('heading', { name: 'Pilih peran Anda hari ini' })

/** The submit button names the role it is about to sign in as, so it moves with the selection. */
const SUBMIT = (page: import('@playwright/test').Page, role: string) =>
  page.getByRole('button', { name: `Masuk sebagai ${role}` })

/** One row of the access matrix, found by the person named in it. */
const ROW = (page: import('@playwright/test').Page, name: string) =>
  page.getByRole('row').filter({ hasText: name })

function resetDemo(): void {
  execFileSync('uv', ['run', 'python', 'scripts/demo_reset.py'], {
    cwd: BACKEND,
    stdio: 'pipe',
  })
}

/**
 * Reset first *and* last: this spec deactivates an account, and leaving one deactivated would
 * lock the next run out of a persona it needs. That is the exact failure `demo_reset.py` exists
 * to prevent, rehearsed here rather than trusted to memory.
 */
test.beforeAll(resetDemo)
test.afterAll(resetDemo)

test.describe('signing in', () => {
  test('the page opens on the reviewer row, already filled, and signs in', async ({ page }) => {
    await page.goto('/login')

    await expect(page.getByText('AKUN SIMULASI', { exact: true })).toBeVisible()
    await expect(page.getByText('DATA SINTETIK', { exact: true })).toBeVisible()

    // The matrix is the control, so the fields arrive filled from the chosen row.
    await expect(page.getByLabel('Email petugas')).toHaveValue(STAFF.reviewer.email)
    await expect(page.getByLabel('Kode demo')).toHaveValue(STAFF.reviewer.passcode)

    await SUBMIT(page, 'Peninjau').click()

    await expect(page.getByRole('heading', { name: 'Antrean Review' })).toBeVisible()
    await expect(page.getByRole('button', { name: /Sari Wulandari/ })).toBeVisible()
  })

  test('the matrix states the role model before anyone signs in', async ({ page }) => {
    await page.goto('/login')

    // The whole reason this page is the matrix: separation of duties, readable at a glance.
    const adminRow = ROW(page, 'Rina Hartati')
    await expect(adminRow.getByText('Tidak')).toHaveCount(5)
    await expect(adminRow.getByText('Boleh')).toHaveCount(1)

    await expect(ROW(page, 'Sari Wulandari').getByText('Tidak')).toHaveCount(2)
    await expect(ROW(page, 'Budi Santoso').getByText('Tidak')).toHaveCount(1)
  })

  test('the page says it is not a security control, and not an official BPJS product', async ({
    page,
  }) => {
    await page.goto('/login')
    await expect(page.getByText(/tidak mengamankan apa pun/)).toBeVisible()
    await expect(page.getByText(/bukan produk atau layanan resmi BPJS Kesehatan/)).toBeVisible()
    await expect(page.getByText(/KATEGORI 2/)).toBeVisible()
  })

  test('the whole page fits one screen — no scrolling at 1440x900', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 })
    await page.goto('/login')
    await expect(LOGIN_HEADING(page)).toBeVisible()

    const overflows = await page.evaluate(
      () => document.documentElement.scrollHeight > window.innerHeight + 1,
    )
    expect(overflows, 'the login page must not scroll').toBe(false)
  })

  test('choosing another row rewrites the fields and renames the button', async ({ page }) => {
    await page.goto('/login')

    await ROW(page, 'Budi Santoso').getByRole('radio').check()

    await expect(page.getByLabel('Email petugas')).toHaveValue(STAFF.senior_reviewer.email)
    await expect(SUBMIT(page, 'Peninjau Senior')).toBeVisible()

    await SUBMIT(page, 'Peninjau Senior').click()
    await expect(page.getByRole('button', { name: /Budi Santoso/ })).toBeVisible()
  })

  test('the whole sign-in works from the keyboard alone', async ({ page }) => {
    await page.goto('/login')

    // The three personas are one radio group, so arrow keys walk down the matrix.
    await ROW(page, 'Sari Wulandari').getByRole('radio').focus()
    await page.keyboard.press('ArrowDown')
    await page.keyboard.press('ArrowDown')

    await expect(page.getByLabel('Email petugas')).toHaveValue(STAFF.admin.email)
    await expect(SUBMIT(page, 'Administrator')).toBeVisible()

    await SUBMIT(page, 'Administrator').focus()
    await page.keyboard.press('Enter')

    await expect(ADMIN_HEADING(page)).toBeVisible()
  })

  test('a wrong passcode is refused and the page never echoes it back', async ({ page }) => {
    await page.goto('/login')

    await page.getByLabel('Kode demo').fill('kode-yang-salah')
    await SUBMIT(page, 'Peninjau').click()

    await expect(page.getByRole('alert')).toContainText('tidak cocok')
    await expect(page.getByRole('heading', { name: 'Antrean Review' })).toHaveCount(0)
    // The refusal must not cost the operator what they typed.
    await expect(page.getByLabel('Email petugas')).toHaveValue(STAFF.reviewer.email)
  })
})

test.describe('what each role sees', () => {
  test('a reviewer sees three menu entries and no user management', async ({ page }) => {
    await signInAs(page, 'reviewer')
    await page.goto('/')

    const nav = page.getByRole('navigation', { name: 'Navigasi utama' })
    await expect(nav.getByRole('link')).toHaveCount(3)
    await expect(nav.getByRole('link', { name: 'Manajemen Pengguna' })).toHaveCount(0)
  })

  test('an administrator sees only user management, and cannot reach a case', async ({
    page,
  }) => {
    await signInAs(page, 'admin')
    await page.goto('/admin/users')

    const nav = page.getByRole('navigation', { name: 'Navigasi utama' })
    await expect(nav.getByRole('link')).toHaveCount(1)

    // Typing the queue's URL is redirected, not shown.
    await page.goto('/')
    await expect(ADMIN_HEADING(page)).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Antrean Review' })).toHaveCount(0)
  })

  test('the API refuses an administrator a case, not merely the UI', async ({ request }) => {
    const queue = await request.get('/v1/cases', {
      headers: { 'X-Actor-Role': 'admin', 'X-Actor-Id': STAFF.admin.userId },
    })
    expect(queue.status()).toBe(403)
    expect((await queue.json()).code).toBe('CASE_ACCESS_FORBIDDEN')
  })

  test('the API refuses a reviewer the roster, not merely the UI', async ({ request }) => {
    const roster = await request.get('/v1/users', {
      headers: { 'X-Actor-Role': 'reviewer', 'X-Actor-Id': STAFF.reviewer.userId },
    })
    expect(roster.status()).toBe(403)
    expect((await roster.json()).code).toBe('USER_MANAGEMENT_FORBIDDEN')
  })
})

test.describe('user management', () => {
  test('changing a role writes a visible audit entry', async ({ page }) => {
    await signInAs(page, 'admin')
    await page.goto('/admin/users')

    const row = page.getByRole('row').filter({ hasText: 'Sari Wulandari' })
    await row.getByRole('combobox').selectOption('senior_reviewer')

    await expect(page.getByText('Peran diubah')).toBeVisible()
    await expect(page.getByText('Peninjau → Peninjau Senior')).toBeVisible()

    // Put it back, so the roster this spec found is the roster it leaves.
    await row.getByRole('combobox').selectOption('reviewer')
    await expect(page.getByText('Peninjau Senior → Peninjau')).toBeVisible()
  })

  test('an administrator cannot deactivate themselves', async ({ page }) => {
    await signInAs(page, 'admin')
    await page.goto('/admin/users')

    const own = page.getByRole('row').filter({ hasText: 'Rina Hartati' })
    await expect(own.getByRole('checkbox')).toBeDisabled()
    await expect(own.getByText('Akun sendiri tidak dapat diubah')).toBeVisible()
  })

  test('a deactivated account is refused at sign-in, with a sentence naming why', async ({
    page,
    browser,
  }) => {
    await signInAs(page, 'admin')
    await page.goto('/admin/users')

    // `click`, not `uncheck`: the checkbox is controlled by the server's answer, so its state
    // changes when the PATCH returns rather than on the click. `uncheck` asserts the flip
    // immediately and fails on a control that is honest about being asynchronous.
    const row = page.getByRole('row').filter({ hasText: 'Budi Santoso' })
    await row.getByRole('checkbox').click()
    await expect(page.getByText('Akun dinonaktifkan')).toBeVisible()
    await expect(row.getByText('Nonaktif')).toBeVisible()

    // A second context, because `signInAs` replays its seed on every navigation in this one —
    // clearing the session here would write it straight back before the guard ran.
    const visitor = await browser.newContext()
    const clean = await visitor.newPage()
    await clean.goto('/login')
    await ROW(clean, 'Budi Santoso').getByRole('radio').check()
    await clean.getByRole('button', { name: 'Masuk sebagai Peninjau Senior' }).click()

    await expect(clean.getByRole('alert')).toContainText('dinonaktifkan')
    await expect(clean.getByRole('alert')).toContainText('PTG-02')
    await visitor.close()

    // Put Budi back, so the next spec — and the next rehearsal — finds a roster it can use.
    await row.getByRole('checkbox').click()
    await expect(page.getByText('Akun diaktifkan kembali')).toBeVisible()
  })
})

test.describe('signing out', () => {
  test('Batal in the confirmation leaves the session alone', async ({ page }) => {
    await signInAs(page, 'reviewer')
    await page.goto('/')

    await page.getByRole('button', { name: /Sari Wulandari/ }).click()
    await page.getByRole('menuitem', { name: /Keluar/ }).click()
    await page.getByRole('dialog').getByRole('button', { name: 'Batal' }).click()

    await expect(page.getByRole('dialog')).toHaveCount(0)
    await expect(page.getByRole('heading', { name: 'Antrean Review' })).toBeVisible()
  })

  test('the profile menu closes on Escape and returns focus to its trigger', async ({ page }) => {
    await signInAs(page, 'reviewer')
    await page.goto('/')

    const trigger = page.getByRole('button', { name: /Sari Wulandari/ })
    await trigger.click()
    await expect(page.getByRole('menu')).toBeVisible()

    await page.keyboard.press('Escape')
    await expect(page.getByRole('menu')).toHaveCount(0)
    await expect(trigger).toBeFocused()
  })

  test('Keluar clears the session and returns to the login page', async ({ page }) => {
    // Signed in through the form rather than seeded: `signInAs` replays its seed on every
    // navigation, which would silently undo the sign-out this spec is about.
    await page.goto('/login')
    await SUBMIT(page, 'Peninjau').click()
    await expect(page.getByRole('heading', { name: 'Antrean Review' })).toBeVisible()

    await page.getByRole('button', { name: /Sari Wulandari/ }).click()
    await page.getByRole('menuitem', { name: /Keluar/ }).click()

    // Signing out asks first: it ends the session and empties any draft, and neither is undoable.
    const confirm = page.getByRole('dialog')
    await expect(confirm.getByText('Keluar dari sesi ini?')).toBeVisible()
    await confirm.getByRole('button', { name: 'Keluar' }).click()

    await expect(LOGIN_HEADING(page)).toBeVisible()
    // Going back to a guarded route does not resurrect the session.
    await page.goto('/')
    await expect(LOGIN_HEADING(page)).toBeVisible()
  })
})

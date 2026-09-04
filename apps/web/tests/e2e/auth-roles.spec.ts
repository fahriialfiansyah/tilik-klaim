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
  test('a reviewer signs in through the form and lands on the queue', async ({ page }) => {
    await page.goto('/login')

    await expect(page.getByText('AKUN SIMULASI')).toBeVisible()
    await expect(page.getByText('DATA SINTETIK')).toBeVisible()

    await page.getByLabel('Email petugas').fill(STAFF.reviewer.email)
    await page.getByLabel('Kode demo').fill(STAFF.reviewer.passcode)
    await page.getByRole('button', { name: 'Masuk', exact: true }).click()

    await expect(page.getByRole('heading', { name: 'Antrean Review' })).toBeVisible()
    await expect(page.getByRole('button', { name: /Sari Wulandari/ })).toBeVisible()
  })

  test('Pakai fills the form, so a persona switch is one click and Enter', async ({ page }) => {
    await page.goto('/login')

    const card = page.getByRole('listitem').filter({ hasText: 'Budi Santoso' })
    await card.getByRole('button', { name: 'Pakai' }).click()

    await expect(page.getByLabel('Email petugas')).toHaveValue(STAFF.senior_reviewer.email)
    await page.keyboard.press('Enter')

    await expect(page.getByRole('button', { name: /Budi Santoso/ })).toBeVisible()
  })

  test('the whole sign-in works from the keyboard alone', async ({ page }) => {
    await page.goto('/login')

    await page.getByLabel('Email petugas').focus()
    await page.keyboard.type(STAFF.admin.email)
    await page.keyboard.press('Tab')
    await page.keyboard.type(STAFF.admin.passcode)
    await page.keyboard.press('Tab')
    await expect(page.getByRole('button', { name: 'Masuk', exact: true })).toBeFocused()
    await page.keyboard.press('Enter')

    await expect(page.getByRole('heading', { name: 'Manajemen Pengguna' })).toBeVisible()
  })

  test('a wrong passcode is refused and the page never echoes it back', async ({ page }) => {
    await page.goto('/login')

    await page.getByLabel('Email petugas').fill(STAFF.reviewer.email)
    await page.getByLabel('Kode demo').fill('kode-yang-salah')
    await page.getByRole('button', { name: 'Masuk', exact: true }).click()

    await expect(page.getByRole('alert')).toContainText('tidak cocok')
    await expect(page.getByRole('heading', { name: 'Antrean Review' })).toHaveCount(0)
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
    await expect(page.getByRole('heading', { name: 'Manajemen Pengguna' })).toBeVisible()
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
  }) => {
    await signInAs(page, 'admin')
    await page.goto('/admin/users')

    const row = page.getByRole('row').filter({ hasText: 'Budi Santoso' })
    await row.getByRole('checkbox').uncheck()
    await expect(page.getByText('Akun dinonaktifkan')).toBeVisible()

    await page.evaluate(() => window.localStorage.removeItem('tilik-session'))
    await page.goto('/login')
    await page.getByLabel('Email petugas').fill(STAFF.senior_reviewer.email)
    await page.getByLabel('Kode demo').fill(STAFF.senior_reviewer.passcode)
    await page.getByRole('button', { name: 'Masuk', exact: true }).click()

    await expect(page.getByRole('alert')).toContainText('dinonaktifkan')
    await expect(page.getByRole('alert')).toContainText('PTG-02')
  })
})

test.describe('signing out', () => {
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
    await signInAs(page, 'reviewer')
    await page.goto('/')

    await page.getByRole('button', { name: /Sari Wulandari/ }).click()
    await page.getByRole('menuitem', { name: /Keluar/ }).click()

    await expect(page.getByRole('heading', { name: 'Masuk' })).toBeVisible()
    // Going back to a guarded route does not resurrect the session.
    await page.goto('/')
    await expect(page.getByRole('heading', { name: 'Masuk' })).toBeVisible()
  })
})

import { defineConfig, devices } from '@playwright/test'

const BASE_URL = process.env.E2E_BASE_URL ?? 'http://localhost:3000'

/**
 * End-to-end configuration.
 *
 * These specs run against the **real API and a seeded database**, not against mocks. The paths
 * they cover — a disposition reaching the audit trail, a stale write being refused without
 * losing input — are exactly the ones a mock would let pass while the real write path was
 * broken. Prepare with:
 *
 *     docker compose up -d db
 *     (cd apps/backend && uv run alembic upgrade head && uv run python scripts/seed_dev.py)
 *     ./scripts/dev.sh          # or run the API and web dev servers separately
 *
 * `reuseExistingServer` is on so a developer's already-running `npm run dev` is used rather
 * than a second one fighting it for port 3000.
 */
export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false,
  /*
   * One worker, deliberately. Every spec writes dispositions to one shared seeded database, and
   * a disposition moves a case's state and bumps its version — two specs on the same case in
   * parallel would produce the version conflict one of them is meant to be testing for.
   */
  workers: 1,
  forbidOnly: Boolean(process.env.CI),
  retries: 0,
  reporter: process.env.CI ? 'line' : [['list']],
  timeout: 30_000,
  expect: { timeout: 7_000 },
  use: {
    baseURL: BASE_URL,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    locale: 'id-ID',
    timezoneId: 'Asia/Jakarta',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    command: 'npm run dev',
    url: BASE_URL,
    reuseExistingServer: true,
    timeout: 120_000,
  },
})

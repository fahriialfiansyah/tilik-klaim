import type { APIRequestContext, Page } from '@playwright/test'
import { expect } from '@playwright/test'

/**
 * Helpers for the case-detail end-to-end paths.
 *
 * Cases are looked up **by risk mode against the live queue**, never by a hard-coded id: the
 * seed script regenerates identifiers on every run, so a pinned id turns "the seed was
 * refreshed" into a failing test that looks like a broken feature.
 */

/** The three seeded personas, mirroring `apps/backend/app/store/seed_users.py`. */
export const STAFF = {
  reviewer: {
    userId: 'usr_sari_wulandari',
    staffToken: 'PTG-01',
    fullName: 'Sari Wulandari',
    email: 'sari.wulandari@rsud-demo.example',
    passcode: 'demo-reviewer-2026',
    role: 'reviewer',
  },
  senior_reviewer: {
    userId: 'usr_budi_santoso',
    staffToken: 'PTG-02',
    fullName: 'Budi Santoso',
    email: 'budi.santoso@rsud-demo.example',
    passcode: 'demo-senior-2026',
    role: 'senior_reviewer',
  },
  admin: {
    userId: 'usr_rina_hartati',
    staffToken: 'PTG-03',
    fullName: 'Rina Hartati',
    email: 'rina.hartati@rsud-demo.example',
    passcode: 'demo-admin-2026',
    role: 'admin',
  },
} as const

export type StaffKey = keyof typeof STAFF

const SESSION_KEY = 'tilik-session'

/**
 * Seed a persona into `localStorage` before the first navigation.
 *
 * Every spec except `auth-roles.spec.ts` uses this: they are about the review flow, not about
 * signing in, and walking the login form at the top of each one would test the same three
 * clicks twenty times while adding a failure mode to specs that are not about it.
 * `auth-roles.spec.ts` signs in for real, through the form, so the path itself stays covered.
 *
 * `addInitScript` runs before any page script, so the store reads it on its very first render
 * and the guard never flashes the login page.
 */
export async function signInAs(page: Page, who: StaffKey = 'reviewer'): Promise<void> {
  const staff = STAFF[who]
  await page.addInitScript(
    ([key, value]) => window.localStorage.setItem(key, value),
    [
      SESSION_KEY,
      JSON.stringify({
        user_id: staff.userId,
        staff_token: staff.staffToken,
        full_name: staff.fullName,
        email: staff.email,
        role: staff.role,
        is_active: true,
        last_signed_in_at: null,
      }),
    ] as const,
  )
}

export type RiskMode =
  | 'PHANTOM_OR_NO_PROCEDURE_EVIDENCE'
  | 'REPEAT_BILLING'
  | 'CLONED_DOCUMENTATION'
  | 'UNBUNDLING_FRAGMENTATION'

type QueueRow = {
  case_id: string
  modes: RiskMode[]
  state: string
  case_version: number
}

async function queue(request: APIRequestContext): Promise<QueueRow[]> {
  const response = await request.get('/v1/cases?page_size=50')
  expect(
    response.ok(),
    'the API must be running and the database seeded — see playwright.config.ts',
  ).toBeTruthy()
  return (await response.json()).items as QueueRow[]
}

/** The first case for a mode that has not been dispositioned yet. */
export async function findOpenCase(
  request: APIRequestContext,
  mode: RiskMode,
): Promise<QueueRow> {
  const rows = await queue(request)
  const match = rows.find(
    (row) => row.modes.includes(mode) && ['SCREENED', 'IN_REVIEW'].includes(row.state),
  )
  expect(
    match,
    `no un-dispositioned ${mode} case in the queue — re-run scripts/seed_dev.py`,
  ).toBeTruthy()
  return match as QueueRow
}

/** Choose an action and a structured reason in the disposition panel. */
export async function fillDisposition(
  page: Page,
  { action, reason, note }: { action: string; reason: string; note?: string },
): Promise<void> {
  await page.getByRole('radio', { name: new RegExp(action) }).click()
  await page.getByLabel('ALASAN TERSTRUKTUR').selectOption(reason)
  if (note) {
    await page.getByLabel('CATATAN BEBAS').fill(note)
  }
}

/** Record a disposition as somebody else, so the case moves under the reviewer's feet. */
export async function dispositionAsAnotherReviewer(
  request: APIRequestContext,
  caseId: string,
  expectedVersion: number,
): Promise<void> {
  const response = await request.post(`/v1/cases/${caseId}/dispositions`, {
    headers: {
      'X-Actor-Role': 'senior_reviewer',
      'X-Actor-Id': STAFF.senior_reviewer.userId,
    },
    data: {
      action: 'REQUEST_EVIDENCE',
      structured_reason: 'Berkas pendukung belum lengkap',
      expected_case_version: expectedVersion,
      requested_evidence: ['Procedure'],
    },
  })
  expect(response.ok(), await response.text()).toBeTruthy()
}

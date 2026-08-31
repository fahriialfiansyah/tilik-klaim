import type { APIRequestContext, Page } from '@playwright/test'
import { expect } from '@playwright/test'

/**
 * Helpers for the case-detail end-to-end paths.
 *
 * Cases are looked up **by risk mode against the live queue**, never by a hard-coded id: the
 * seed script regenerates identifiers on every run, so a pinned id turns "the seed was
 * refreshed" into a failing test that looks like a broken feature.
 */

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
    headers: { 'X-Actor-Role': 'senior_reviewer' },
    data: {
      action: 'REQUEST_EVIDENCE',
      structured_reason: 'Berkas pendukung belum lengkap',
      expected_case_version: expectedVersion,
      requested_evidence: ['Procedure'],
    },
  })
  expect(response.ok(), await response.text()).toBeTruthy()
}

import type { Role } from '@/features/auth/types'

/**
 * The three demo accounts, printed on the login page.
 *
 * **These passcodes are not secrets, by construction.** The whole sign-in is persona selection
 * with a credential-shaped interface (ADR-0006 § 3), and the page displays the value beside the
 * account it belongs to. Nothing here protects anything, so nothing here belongs in an
 * environment variable — a real credential would, and `apps/backend/.env.example` documents its
 * name with an empty value.
 *
 * Held here rather than fetched, because the endpoint that would serve them would be an endpoint
 * whose purpose is to hand back passcodes. `GET /v1/users` is admin-only and returns no passcode
 * at all; this list mirrors `apps/backend/app/store/seed_users.py`, and
 * `demo-accounts.test.ts` asserts the two agree.
 *
 * Emails use the RFC 2606 reserved `.example` TLD, so no address can ever resolve.
 */
export type DemoAccount = {
  readonly staffCode: string
  readonly fullName: string
  readonly email: string
  readonly role: Role
  readonly passcode: string
}

export const DEMO_ACCOUNTS: readonly DemoAccount[] = [
  {
    staffCode: 'PTG-01',
    fullName: 'Sari Wulandari',
    email: 'sari.wulandari@rsud-demo.example',
    role: 'reviewer',
    passcode: 'demo-reviewer-2026',
  },
  {
    staffCode: 'PTG-02',
    fullName: 'Budi Santoso',
    email: 'budi.santoso@rsud-demo.example',
    role: 'senior_reviewer',
    passcode: 'demo-senior-2026',
  },
  {
    staffCode: 'PTG-03',
    fullName: 'Rina Hartati',
    email: 'rina.hartati@rsud-demo.example',
    role: 'admin',
    passcode: 'demo-admin-2026',
  },
] as const

/** What `Salin` puts on the clipboard: enough to sign in, in one line. */
export function credentialLine(account: DemoAccount): string {
  return `${account.email} · ${account.passcode}`
}

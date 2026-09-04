import type { Role } from '@/features/auth/types'

/**
 * What each role may reach, mirroring the server's matrix in `app/service/access.py`.
 *
 * **This is not the access control.** Hiding a route is a courtesy that keeps a reviewer from
 * clicking into a refusal; the refusal itself is the server's, with a stable error code, and
 * `apps/backend/tests/test_access.py` asserts every row of it. If the two ever disagree, the
 * server is right and this file is the defect.
 */
export const CASE_ROLES: readonly Role[] = ['reviewer', 'senior_reviewer']

/** Where each role lands after signing in, and where a forbidden route redirects to. */
export const LANDING_ROUTE: Readonly<Record<Role, string>> = {
  reviewer: '/',
  senior_reviewer: '/',
  admin: '/admin/users',
}

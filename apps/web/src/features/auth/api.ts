import type { SessionResponse } from '@/features/auth/types'
import { request } from '@/lib/http'

/**
 * Select a persona.
 *
 * Nothing is issued: no token, no cookie, no server-side session. The response is the account,
 * and the client keeps it. See ADR-0006 § 3 for why this is credential-shaped but is not
 * authentication, and why saying so plainly is the point rather than an omission.
 */
export async function startSession(email: string, passcode: string): Promise<SessionResponse> {
  return request<SessionResponse>('/auth/session', {
    method: 'POST',
    body: JSON.stringify({ email, passcode }),
  })
}

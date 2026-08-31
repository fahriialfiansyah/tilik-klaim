import type {
  AuditResponse,
  CaseDetail,
  DispositionRequest,
  DispositionResponse,
} from '@/features/review/case-detail/types'
import { request } from '@/lib/http'

/**
 * The actor's role travels in a header.
 *
 * This is **role simulation for a prototype**, matching what the backend expects, and it is not
 * authentication — the demo has no login and `docs/canonical/01_product_decision.md` puts
 * enterprise IAM out of scope. Naming it plainly is deliberate: dressing it up as a token would
 * invite someone to mistake it for a security control.
 */
export const ACTOR_ROLE = 'reviewer'
const ACTOR_HEADER = { 'X-Actor-Role': ACTOR_ROLE }

export async function fetchCaseDetail(caseId: string): Promise<CaseDetail> {
  return request<CaseDetail>(`/cases/${encodeURIComponent(caseId)}`)
}

export async function fetchAudit(caseId: string): Promise<AuditResponse> {
  return request<AuditResponse>(`/cases/${encodeURIComponent(caseId)}/audit`, {
    headers: ACTOR_HEADER,
  })
}

/**
 * Record a decision.
 *
 * `expected_case_version` is mandatory on the wire and mandatory here. A save that omitted it
 * would overwrite whatever a colleague recorded in the meantime, which
 * `brief/04_DETAIL_KASUS_DISPOSISI.md` § 4.3 calls an accountability failure rather than a
 * concurrency bug. On rejection the caller keeps the reviewer's input — this function throws and
 * changes nothing.
 */
export async function saveDisposition(
  caseId: string,
  body: DispositionRequest,
): Promise<DispositionResponse> {
  return request<DispositionResponse>(`/cases/${encodeURIComponent(caseId)}/dispositions`, {
    method: 'POST',
    headers: ACTOR_HEADER,
    body: JSON.stringify(body),
  })
}

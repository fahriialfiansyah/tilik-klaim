import type {
  AuditResponse,
  CaseDetail,
  DispositionRequest,
  DispositionResponse,
} from '@/features/review/case-detail/types'
import { request } from '@/lib/http'

/*
 * The actor headers used to be a hardcoded `ACTOR_ROLE = 'reviewer'` constant here, sent on
 * every call whoever was looking at the screen. Since ADR-0006 they come from the signed-in
 * persona and are attached by `src/lib/http.ts` for every request, so there is nothing left for
 * this module to add.
 */

export async function fetchCaseDetail(caseId: string): Promise<CaseDetail> {
  return request<CaseDetail>(`/cases/${encodeURIComponent(caseId)}`)
}

export async function fetchAudit(caseId: string): Promise<AuditResponse> {
  return request<AuditResponse>(`/cases/${encodeURIComponent(caseId)}/audit`)
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
    body: JSON.stringify(body),
  })
}

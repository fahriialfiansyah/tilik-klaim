import type { VersionStamp } from '@/modules/engine-version/useEngineVersion'

/**
 * Wire types mirroring `apps/backend/app/dto/`. Names match the JSON exactly — snake_case is
 * kept rather than mapped, so a field can be traced from the network tab to the DTO without a
 * translation step in between.
 */

/** The four officially listed facility risk modes. */
export const RISK_MODES = [
  'PHANTOM_OR_NO_PROCEDURE_EVIDENCE',
  'REPEAT_BILLING',
  'CLONED_DOCUMENTATION',
  'UNBUNDLING_FRAGMENTATION',
] as const
export type RiskMode = (typeof RISK_MODES)[number]

/**
 * Priority bands, most urgent first.
 *
 * `NO_OBSERVED_RISK` means no selected detector fired at this engine version. It must never be
 * rendered as "clean" or "safe" — the system is not entitled to that claim.
 */
export const PRIORITY_BANDS = [
  'DETERMINISTIC_CONFLICT',
  'HIGH_PRIORITY_SIGNAL',
  'NEEDS_CONTEXT',
  'NO_OBSERVED_RISK',
] as const
export type PriorityBand = (typeof PRIORITY_BANDS)[number]

export const CASE_STATES = [
  'NEW',
  'SCREENED',
  'IN_REVIEW',
  'EVIDENCE_REQUESTED',
  'DISMISSED',
  'CONFIRMED_ANOMALY',
  'ESCALATED',
  'INVALID_INPUT',
] as const
export type CaseState = (typeof CASE_STATES)[number]

export type EvidenceCompleteness = {
  readonly supported_lines: number
  readonly total_lines: number
  readonly missing_reference_count: number
  readonly bundle_complete: boolean
}

/** One queue row. Pseudonymous fields only, and no narrative text — enforced server-side. */
export type CaseSummary = {
  readonly reason_sentence: string
  readonly modes: readonly RiskMode[]
  readonly case_id: string
  readonly participant_token: string
  readonly provider_token: string
  readonly evidence_completeness: EvidenceCompleteness
  readonly total_amount: string
  readonly currency: string
  readonly created_at: string
  readonly band: PriorityBand
  readonly state: CaseState
  readonly case_version: number
}

/** The five operational metrics above the queue. Exactly five, by design. */
export type QueueMetrics = {
  readonly awaiting_review: number
  readonly deterministic_conflicts: number
  readonly evidence_requested: number
  readonly median_time_in_queue_hours: number
  readonly versions: VersionStamp
}

export type PageInfo = {
  readonly page: number
  readonly page_size: number
  readonly total_items: number
  readonly total_pages: number
}

export type CaseQueueResponse = {
  readonly metrics: QueueMetrics
  readonly items: readonly CaseSummary[]
  readonly page: PageInfo
}

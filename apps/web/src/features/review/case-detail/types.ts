import type {
  CaseState,
  EvidenceCompleteness,
  PriorityBand,
  RiskMode,
} from '@/features/review/shared/types'
import type { VersionStamp } from '@/modules/engine-version/useEngineVersion'

/**
 * Wire types for `GET /v1/cases/{id}`, `POST /v1/cases/{id}/dispositions`, and
 * `GET /v1/cases/{id}/audit`. snake_case is kept, matching `shared/types.ts`, so a field can be
 * traced from the network tab to `apps/backend/app/dto/` without a translation step.
 */

export const RESOURCE_TYPES = [
  'Claim',
  'ClaimLine',
  'Encounter',
  'Condition',
  'Procedure',
  'Medication',
  'Diagnostic',
  'Document',
  'Account',
  'ChargeItem',
  'Invoice',
  'Episode',
  'Practitioner',
] as const
export type ResourceType = (typeof RESOURCE_TYPES)[number]

/**
 * How a billed line stands against the evidence.
 *
 * `NOT_ASSESSABLE` and `UNSUPPORTED` are different findings and lead to different actions —
 * asking for a document versus questioning whether a service happened. The UI must never draw
 * them the same way.
 */
export const SUPPORT_STATES = [
  'SUPPORTED',
  'PARTIALLY_SUPPORTED',
  'UNSUPPORTED',
  'NOT_ASSESSABLE',
] as const
export type SupportState = (typeof SUPPORT_STATES)[number]

/**
 * Why a referenced resource can or cannot be shown in full.
 *
 * `MISSING` is the only one that is a defect. Rendering the other three as an empty panel
 * would hide a real broken evidence trail among two deliberate boundaries.
 */
export const SOURCE_AVAILABILITIES = [
  'PRESENT',
  'RELATED_BUNDLE',
  'NOT_STORED',
  'MISSING',
] as const
export type SourceAvailability = (typeof SOURCE_AVAILABILITIES)[number]

export const DISPOSITION_ACTIONS = [
  'REJECT_SIGNAL',
  'REQUEST_EVIDENCE',
  'CONFIRM_ANOMALY',
  'ESCALATE',
] as const
export type DispositionAction = (typeof DISPOSITION_ACTIONS)[number]

export type EvidenceRef = {
  readonly resource_type: ResourceType
  readonly resource_id: string
  readonly label: string
}

/** A fact that argues against the reason it accompanies — the sentence, not only the pointer. */
export type CounterEvidenceNote = {
  readonly note: string
  readonly refs: readonly EvidenceRef[]
}

export type Reason = {
  readonly code: string
  readonly mode: RiskMode
  readonly sentence: string
  readonly deterministic: boolean
  /** Resource types that should stand behind the billed line, from the reason catalog. */
  readonly expected_support: readonly ResourceType[]
  readonly evidence: readonly EvidenceRef[]
  readonly counter_evidence: readonly EvidenceRef[]
  readonly counter_evidence_notes: readonly CounterEvidenceNote[]
  readonly component_scores: Readonly<Record<string, number>>
  readonly ruleset_version: string
}

export type BandExplanation = {
  readonly band: PriorityBand
  readonly basis: string
  readonly caps_applied: readonly string[]
}

export type ClaimLineView = {
  readonly line_id: string
  readonly code: string
  readonly description: string
  readonly quantity: string
  readonly line_amount: string
  readonly service_at: string
  readonly support_state: SupportState
}

export type TimelineEvent = {
  readonly occurred_at: string
  readonly kind: string
  readonly label: string
  readonly resource: EvidenceRef | null
}

export type ComparisonField = {
  readonly field_name: string
  readonly left_value: string
  readonly right_value: string
  readonly matches: boolean
}

export type ComparisonCandidate = {
  readonly candidate_case_id: string | null
  readonly candidate_claim_id: string
  readonly fields: readonly ComparisonField[]
  readonly overlap_start: string | null
  readonly overlap_end: string | null
  readonly similarity_components: Readonly<Record<string, number>>
  readonly template_caveat: string | null
}

export type SourceField = {
  readonly name: string
  readonly value: string
}

export type SourceResource = {
  readonly resource_type: ResourceType
  readonly resource_id: string
  readonly label: string
  readonly availability: SourceAvailability
  readonly fields: readonly SourceField[]
}

export type CaseDetail = {
  readonly case_id: string
  readonly case_version: number
  readonly state: CaseState
  readonly participant_token: string
  readonly provider_token: string
  readonly total_amount: string
  readonly currency: string
  readonly encounter_start: string
  readonly encounter_end: string | null
  readonly primary_reason: Reason | null
  readonly reasons: readonly Reason[]
  readonly band: BandExplanation
  readonly lines: readonly ClaimLineView[]
  readonly timeline: readonly TimelineEvent[]
  readonly comparisons: readonly ComparisonCandidate[]
  readonly evidence_completeness: EvidenceCompleteness
  readonly sources: readonly SourceResource[]
  readonly suggested_action: DispositionAction | null
  readonly versions: VersionStamp
}

export type DispositionRequest = {
  readonly action: DispositionAction
  readonly structured_reason: string
  readonly note?: string
  readonly expected_case_version: number
  readonly requested_evidence?: readonly ResourceType[]
}

export type DispositionResponse = {
  readonly event_id: string
  readonly case_id: string
  readonly new_state: CaseState
  readonly new_case_version: number
  readonly recorded_at: string
}

export type AuditEvent = {
  readonly event_id: string
  readonly case_id: string
  readonly event_kind: string
  readonly actor_role: string
  readonly action: DispositionAction | null
  readonly structured_reason: string | null
  readonly note: string | null
  readonly evidence: readonly EvidenceRef[]
  readonly state_before: CaseState | null
  readonly state_after: CaseState | null
  readonly supersedes_event_id: string | null
  readonly versions: VersionStamp
  readonly occurred_at: string
}

export type AuditResponse = {
  readonly case_id: string
  readonly events: readonly AuditEvent[]
}

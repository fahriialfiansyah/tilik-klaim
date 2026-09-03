import type { EvidenceRef } from '@/features/review/case-detail/types'
import type { VersionStamp } from '@/modules/engine-version/useEngineVersion'

/**
 * Wire types for `GET /v1/cases/{id}/briefing` (ADR-0005). snake_case kept, mirroring
 * `apps/backend/app/dto/briefing.py` field for field.
 *
 * Nothing here can carry a band, a score, or a state: the backend DTO has no such field, and a
 * `confidence` is a word rather than a number on purpose — a number beside a risk band reads as
 * a second score.
 */

export const OBSERVATION_KINDS = [
  'EVIDENCE_GAP',
  'CORROBORATION',
  'COUNTER_EVIDENCE',
  'COMPARISON',
  'TIMELINE',
  'COMPLETENESS',
] as const
export type ObservationKind = (typeof OBSERVATION_KINDS)[number]

export type Confidence = 'STATED' | 'INFERRED'
export type GeneratedBy = 'LLM' | 'TEMPLATE'
export type BriefingPhase = 'STARTED' | 'READING' | 'VALIDATING' | 'DONE'

export type BriefingObservation = {
  readonly statement: string
  readonly kind: ObservationKind
  readonly source_refs: readonly EvidenceRef[]
  readonly reason_code: string | null
  readonly confidence: Confidence
}

export type BriefingQuestion = {
  readonly question: string
  readonly why_it_matters: string
  readonly source_refs: readonly EvidenceRef[]
}

export type ToolCallRecord = {
  readonly tool: string
  readonly arguments: Readonly<Record<string, string>>
}

export type CaseBriefing = {
  readonly case_id: string
  readonly case_version: number
  readonly observations: readonly BriefingObservation[]
  readonly open_questions: readonly BriefingQuestion[]
  readonly uncertainty_note: string
  readonly generated_by: GeneratedBy
  readonly model_id: string | null
  readonly prompt_version: string
  readonly validation_rejected: boolean
  readonly rejection_reason: string | null
  readonly tool_calls: readonly ToolCallRecord[]
  readonly versions: VersionStamp
}

/** One Server-Sent Event, tagged by its `event:` name. */
export type BriefingEvent =
  | { readonly name: 'status'; readonly data: { readonly phase: BriefingPhase; readonly detail: string } }
  | { readonly name: 'tool'; readonly data: ToolCallRecord }
  | { readonly name: 'observation'; readonly data: { readonly observation: BriefingObservation } }
  | { readonly name: 'done'; readonly data: { readonly briefing: CaseBriefing } }
  | { readonly name: 'error'; readonly data: { readonly code: string; readonly detail: string } }

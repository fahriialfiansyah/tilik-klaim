import type { BriefingPhase, GeneratedBy, ToolCallRecord } from '@/features/review/case-briefing/types'
import type { ResourceType } from '@/features/review/case-detail/types'
import type { CaseSummary } from '@/features/review/shared/types'
import type { VersionStamp } from '@/modules/engine-version/useEngineVersion'

/**
 * Wire types for `POST /v1/assistant/answers` (ADR-0007). snake_case kept, mirroring
 * `apps/backend/app/dto/assistant.py` field for field.
 *
 * Nothing here can carry a score or a state transition. A statement cannot exist without a
 * citation on the server, and the type says the same: `citations` is never optional.
 */

export type ScopeKind = 'QUEUE' | 'CASE'

/** What one turn may read. Always visible on screen, and always the reviewer's choice. */
export type AssistantScope =
  | { readonly kind: 'QUEUE'; readonly case_id?: null }
  | { readonly kind: 'CASE'; readonly case_id: string }

export const QUEUE_SCOPE: AssistantScope = { kind: 'QUEUE' }

export type AnswerKind = 'ANSWER' | 'REFUSAL' | 'HELP'

export type AnswerIntent =
  | 'QUEUE_OVERVIEW'
  | 'WHERE_TO_START'
  | 'CASES_MATCHING'
  | 'CASE_OVERVIEW'
  | 'WHY_RAISED'
  | 'MISSING_EVIDENCE'
  | 'COUNTER_EVIDENCE'
  | 'TIMELINE'
  | 'COMPARISON'
  | 'OPEN_QUESTION'
  | 'OUT_OF_SCOPE'
  | 'UNRECOGNISED'

export type RefusalTopic = 'VERDICT' | 'DECISION' | 'CLINICAL' | 'IDENTITY' | 'INSTRUCTIONS'

export type CitationKind = 'QUEUE' | 'CASE' | 'RESOURCE'

export type Citation = {
  readonly kind: CitationKind
  readonly case_id: string | null
  readonly resource_type: ResourceType | null
  readonly resource_id: string | null
  readonly label: string
}

export type AssistantStatement = {
  readonly text: string
  readonly citations: readonly Citation[]
}

/** A queue row, verbatim, with the position the queue itself gave it. */
export type CaseCard = {
  readonly queue_position: number
  readonly case: CaseSummary
}

export type AssistantAnswer = {
  readonly question: string
  readonly scope: AssistantScope
  readonly kind: AnswerKind
  readonly intent: AnswerIntent
  readonly refusal_topic: RefusalTopic | null
  readonly notice: string | null
  readonly statements: readonly AssistantStatement[]
  readonly cases: readonly CaseCard[]
  readonly uncertainty_note: string
  readonly generated_by: GeneratedBy
  readonly model_id: string | null
  readonly prompt_version: string
  readonly validation_rejected: boolean
  readonly rejection_reason: string | null
  readonly tool_calls: readonly ToolCallRecord[]
  readonly versions: VersionStamp
}

export type HistoryTurn = { readonly question: string; readonly answer: string }

export type AssistantQuestion = {
  readonly question: string
  readonly scope: AssistantScope
  readonly history: readonly HistoryTurn[]
}

/** One Server-Sent Event, tagged by its `event:` name. */
export type AssistantEvent =
  | { readonly name: 'status'; readonly data: { readonly phase: BriefingPhase; readonly detail: string } }
  | { readonly name: 'tool'; readonly data: ToolCallRecord }
  | { readonly name: 'done'; readonly data: { readonly answer: AssistantAnswer } }
  | { readonly name: 'error'; readonly data: { readonly code: string; readonly detail: string } }

/** Server limits, mirrored so the input can stop a reviewer before the server has to. */
export const MAX_QUESTION_CHARS = 500
export const MAX_HISTORY_TURNS = 3
export const MAX_HISTORY_ANSWER_CHARS = 1500

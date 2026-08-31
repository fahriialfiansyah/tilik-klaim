import type { BandExplanation, Reason } from '@/features/review/case-detail/types'
import type { CaseState } from '@/features/review/shared/types'
import type { VersionStamp } from '@/modules/engine-version/useEngineVersion'

/**
 * Wire types for `POST /v1/bundles` and `POST /v1/bundles/{id}/screen`, plus the shape of the
 * demo samples under `public/samples/`.
 *
 * snake_case is kept, matching the other feature folders, so a field can be traced from the
 * network tab to `apps/backend/app/dto/bundles.py` without a translation step.
 */

/**
 * Three outcomes, not two.
 *
 * `VALID_WITH_NOTES` is **not** a softer `INVALID`. An incomplete record and a
 * billed-but-unevidenced service look identical at the schema level, and collapsing them is how
 * this system would manufacture a false accusation — so the distinction is in the type, and the
 * screen has to draw all three differently.
 */
export const VALIDATION_STATUSES = ['VALID', 'VALID_WITH_NOTES', 'INVALID'] as const
export type ValidationStatus = (typeof VALIDATION_STATUSES)[number]

export type ResourceCount = {
  readonly resource_type: string
  readonly count: number
}

/** One problem found in a submission, pointed at a specific resource. */
export type ValidationIssue = {
  readonly code: string
  readonly resource_type: string | null
  readonly resource_id: string | null
  readonly detail: string
}

export type IngestBundleResponse = {
  readonly ingestion_id: string
  readonly status: ValidationStatus
  readonly input_hash: string
  readonly resource_counts: readonly ResourceCount[]
  readonly issues: readonly ValidationIssue[]
  readonly completeness_notes: readonly string[]
  readonly is_screenable: boolean
  /** Set when this exact payload and engine version were already screened. */
  readonly existing_case_id: string | null
  readonly schema_version: string
}

export type ScreenResponse = {
  readonly case_id: string
  readonly case_version: number
  readonly state: CaseState
  readonly primary_reason: Reason | null
  readonly reasons: readonly Reason[]
  readonly band: BandExplanation
  readonly versions: VersionStamp
  readonly latency_ms: number
}

/** One row of `public/samples/index.json`. */
export type SampleSummary = {
  readonly scenario: string
  readonly label: string
  readonly description: string
  /**
   * How many prior claims this scenario needs ingested first.
   *
   * Repeat billing, cloned documentation, and unbundling are only visible *across* claims, so
   * those samples carry a prior bundle. The screen says so rather than submitting it silently.
   */
  readonly history_count: number
}

/** One file under `public/samples/`. Never carries the fixture's expected outcome. */
export type SamplePayload = {
  readonly scenario: string
  readonly demo: {
    readonly bundle_id: string
    readonly scenario_label: string
    readonly description: string
  }
  readonly history: readonly unknown[]
  readonly bundle: unknown
}

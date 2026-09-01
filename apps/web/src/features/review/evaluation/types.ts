import type { RiskMode } from '@/features/review/shared/types'
import type { VersionStamp } from '@/modules/engine-version/useEngineVersion'

/**
 * Wire types mirroring `apps/backend/app/dto/evaluations.py`. snake_case is kept so a value can
 * be traced from the network tab to the DTO without a translation step.
 *
 * **A baseline or a mode the API omits was not measured.** The response carries only rows whose
 * metrics are defined; anything missing is rendered as "tidak terukur", never as a zero. Zero
 * would say the measurement was made and came out empty, which is a different and false claim.
 */

/** The four approaches compared, in the order the evaluation plan lists them. */
export const BASELINE_IDS = [
  'B0_RANDOM',
  'B1_RULES_ONLY',
  'B2_STATISTICAL_ONLY',
  'HYBRID',
] as const
export type BaselineId = (typeof BASELINE_IDS)[number]

export type BaselineMetrics = {
  readonly baseline: string
  readonly macro_f1: number
  readonly pr_auc: number
  readonly precision_at_k: number
  readonly recall_at_k: number
  readonly false_positives_per_100_clean: number
}

export type ModeMetrics = {
  readonly mode: RiskMode
  readonly precision: number
  readonly recall: number
  readonly f1: number
  readonly support: number
}

export type RunManifest = {
  readonly dataset_hash: string
  readonly generator_version: string
  readonly split_manifest_hash: string
  readonly feature_version: string
  readonly ruleset_version: string
  readonly model_version: string
  readonly threshold_logic: string
  readonly code_commit: string
  readonly environment_hash: string
  readonly artifact_hashes: Readonly<Record<string, string>>
}

export type LimitationsCard = {
  readonly demonstrates: readonly string[]
  readonly does_not_demonstrate: readonly string[]
  readonly mandatory_statement: string
}

export type EvaluationResponse = {
  readonly run_id: string
  readonly completed_at: string
  readonly data_class: string
  readonly baselines: readonly BaselineMetrics[]
  readonly per_mode: readonly ModeMetrics[]
  readonly latency_p50_ms: number
  readonly latency_p95_ms: number
  readonly manifest: RunManifest
  readonly limitations: LimitationsCard
  readonly versions: VersionStamp
}

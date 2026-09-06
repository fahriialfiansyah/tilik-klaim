import { useTranslation } from 'react-i18next'

import type { BaselineId } from '@/features/review/evaluation/types'
import { translateOr } from '@/modules/i18n/translateOr'

/**
 * Labels for the evaluation page. Identifiers stay English; everything a reader reads is
 * resolved through i18next.
 *
 * The metric names are deliberately spelled out rather than left as `P@K` or `PR-AUC`. This page
 * is read by the proposal team as well as by engineers, and an abbreviation nobody can expand is
 * a number nobody can defend.
 */

export function useBaselineLabel(): (baseline: BaselineId) => string {
  const { t } = useTranslation('evaluation')
  return (baseline) => t(`baseline.${baseline}` as 'baseline.HYBRID')
}

export function useBaselineHint(): (baseline: BaselineId) => string {
  const { t } = useTranslation('evaluation')
  return (baseline) => t(`baselineHint.${baseline}` as 'baselineHint.HYBRID')
}

export type MetricKey =
  | 'macro_f1'
  | 'pr_auc'
  | 'precision_at_k'
  | 'recall_at_k'
  | 'false_positives_per_100_clean'

export function useMetricLabel(): (metric: MetricKey) => string {
  const { t } = useTranslation('evaluation')
  return (metric) => t(`metric.${metric}` as 'metric.macro_f1')
}

/**
 * The canonical limitations rows, in the reader's language.
 *
 * `docs/canonical/06_evaluation_plan.md` states these rows in English and the artifact
 * `LIMITATIONS.md` carries them **verbatim**, because a canonical row paraphrased in an artifact
 * stops being quotable. The page renders a translation and the artifact keeps the original — so
 * in English the two now agree word for word, which is the point rather than a coincidence.
 *
 * The lookup falls back to the source string. A caveat the runner adds later shows up in
 * English rather than vanishing — a missing limitation is far worse than an untranslated one.
 */
export function toReadable(line: string): string {
  return translateOr(`evaluation:limitation.${line}`, line)
}

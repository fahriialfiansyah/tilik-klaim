import { BASELINE_HINT, BASELINE_LABEL, METRIC_LABEL } from '@/features/review/evaluation/labels'
import type { ChartRow } from '@/features/review/evaluation/components/MetricBarChart'
import type { MetricColumn, MetricRow } from '@/features/review/evaluation/components/MetricTable'
import {
  BASELINE_IDS,
  type BaselineId,
  type EvaluationResponse,
} from '@/features/review/evaluation/types'
import { MODE_LABELS } from '@/features/review/shared/labels'
import { RISK_MODES } from '@/features/review/shared/types'

/**
 * Turn one response into the rows every widget renders.
 *
 * Both the tables and the charts are built here, from the same objects, which is what makes
 * "chart values = table values" (`sprint/00-app-spec.md` § 6 rule 2) a property of the code
 * rather than a convention to remember.
 *
 * **The four baselines and four modes are always listed**, in their canonical order, whether or
 * not the response carries them. A baseline the API omitted was not measured, and it appears
 * with `null` — which every widget renders as "tidak terukur". Iterating the response instead
 * would make an unmeasured baseline silently vanish from the comparison.
 */

export const BASELINE_COLUMNS: readonly MetricColumn[] = [
  { key: 'macro_f1', label: METRIC_LABEL.macro_f1 },
  { key: 'pr_auc', label: METRIC_LABEL.pr_auc },
  { key: 'precision_at_k', label: METRIC_LABEL.precision_at_k },
  { key: 'recall_at_k', label: METRIC_LABEL.recall_at_k },
  {
    key: 'false_positives_per_100_clean',
    label: METRIC_LABEL.false_positives_per_100_clean,
  },
]

export const MODE_COLUMNS: readonly MetricColumn[] = [
  { key: 'precision', label: 'Ketepatan' },
  { key: 'recall', label: 'Keterpanggilan' },
  { key: 'f1', label: 'F1' },
  { key: 'support', label: 'Jumlah kasus', format: 'count' },
]

export function baselineRows(evaluation: EvaluationResponse): readonly MetricRow[] {
  const measured = new Map(evaluation.baselines.map((row) => [row.baseline, row]))
  return BASELINE_IDS.map((baseline) => {
    const row = measured.get(baseline)
    return {
      key: baseline,
      label: BASELINE_LABEL[baseline],
      hint: BASELINE_HINT[baseline],
      values: {
        macro_f1: row?.macro_f1 ?? null,
        pr_auc: row?.pr_auc ?? null,
        precision_at_k: row?.precision_at_k ?? null,
        recall_at_k: row?.recall_at_k ?? null,
        false_positives_per_100_clean: row?.false_positives_per_100_clean ?? null,
      },
    }
  })
}

export function modeRows(evaluation: EvaluationResponse): readonly MetricRow[] {
  const measured = new Map(evaluation.per_mode.map((row) => [row.mode, row]))
  return RISK_MODES.map((mode) => {
    const row = measured.get(mode)
    return {
      key: mode,
      label: MODE_LABELS[mode],
      values: {
        precision: row?.precision ?? null,
        recall: row?.recall ?? null,
        f1: row?.f1 ?? null,
        support: row?.support ?? null,
      },
    }
  })
}

/** Widget 5 — false positives per 100 clean claims, one bar per baseline. */
export function falsePositiveChartRows(evaluation: EvaluationResponse): readonly ChartRow[] {
  return chartRowsFor(evaluation, 'false_positives_per_100_clean')
}

/** Widget 6 — precision at the fixed review budget, one bar per baseline. */
export function precisionAtBudgetChartRows(evaluation: EvaluationResponse): readonly ChartRow[] {
  return chartRowsFor(evaluation, 'precision_at_k')
}

function chartRowsFor(
  evaluation: EvaluationResponse,
  column: string,
): readonly ChartRow[] {
  return baselineRows(evaluation).map((row) => ({
    key: row.key,
    label: BASELINE_LABEL[row.key as BaselineId],
    value: row.values[column],
  }))
}

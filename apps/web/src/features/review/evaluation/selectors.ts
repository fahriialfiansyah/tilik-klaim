import type { ChartRow } from '@/features/review/evaluation/components/MetricBarChart'
import type { MetricColumn, MetricRow } from '@/features/review/evaluation/components/MetricTable'
import {
  BASELINE_IDS,
  type BaselineId,
  type EvaluationResponse,
} from '@/features/review/evaluation/types'
import { translateOr } from '@/modules/i18n/translateOr'
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
 * with `null` — which every widget renders as "not measured". Iterating the response instead
 * would make an unmeasured baseline silently vanish from the comparison.
 *
 * The column lists are functions rather than constants because their headings are words: a
 * module-level array would freeze them in whichever language happened to be active when the
 * bundle first evaluated, and the table would keep those headings after the header switch. The
 * *order* still lives here, where it belongs — a translator cannot reorder a table by editing
 * a JSON object.
 */

const BASELINE_COLUMN_KEYS = [
  'macro_f1',
  'pr_auc',
  'precision_at_k',
  'recall_at_k',
  'false_positives_per_100_clean',
] as const

export function baselineColumns(): readonly MetricColumn[] {
  return BASELINE_COLUMN_KEYS.map((key) => ({
    key,
    label: translateOr(`evaluation:metric.${key}`, key),
  }))
}

export function modeColumns(): readonly MetricColumn[] {
  return [
    { key: 'precision', label: translateOr('evaluation:modeColumn.precision', 'precision') },
    { key: 'recall', label: translateOr('evaluation:modeColumn.recall', 'recall') },
    { key: 'f1', label: translateOr('evaluation:modeColumn.f1', 'f1') },
    {
      key: 'support',
      label: translateOr('evaluation:modeColumn.support', 'support'),
      format: 'count',
    },
  ]
}

export function baselineRows(evaluation: EvaluationResponse): readonly MetricRow[] {
  const measured = new Map(evaluation.baselines.map((row) => [row.baseline, row]))
  return BASELINE_IDS.map((baseline) => {
    const row = measured.get(baseline)
    return {
      key: baseline,
      label: translateOr(`evaluation:baseline.${baseline}`, baseline),
      hint: translateOr(`evaluation:baselineHint.${baseline}`, ''),
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
      label: translateOr(`review:mode.${mode}`, mode),
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
    label: translateOr(`evaluation:baseline.${row.key as BaselineId}`, row.key),
    value: row.values[column],
  }))
}

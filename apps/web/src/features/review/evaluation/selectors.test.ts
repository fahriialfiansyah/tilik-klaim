import { describe, expect, test } from 'vitest'

import { formatMetric } from '@/features/review/evaluation/format'
import {
  baselineRows,
  falsePositiveChartRows,
  modeRows,
  precisionAtBudgetChartRows,
} from '@/features/review/evaluation/selectors'
import { EVALUATION_FIXTURE } from '@/features/review/evaluation/test-fixtures'
import { BASELINE_IDS } from '@/features/review/evaluation/types'
import { RISK_MODES } from '@/features/review/shared/types'

describe('every baseline and every mode is listed, measured or not', () => {
  test('a baseline the API omitted still appears, with null values', () => {
    // Arrange & Act
    const rows = baselineRows(EVALUATION_FIXTURE)

    // Assert
    expect(rows.map((row) => row.key)).toEqual([...BASELINE_IDS])
    const random = rows.find((row) => row.key === 'B0_RANDOM')
    expect(random?.values.macro_f1).toBeNull()
  })

  test('an omitted value is null rather than zero', () => {
    const random = baselineRows(EVALUATION_FIXTURE).find((row) => row.key === 'B0_RANDOM')

    expect(random?.values.precision_at_k).not.toBe(0)
    expect(random?.values.precision_at_k).toBeNull()
  })

  test('a mode absent from the run still appears, with null values', () => {
    const rows = modeRows(EVALUATION_FIXTURE)

    expect(rows.map((row) => row.key)).toEqual([...RISK_MODES])
    const cloned = rows.find((row) => row.key === 'CLONED_DOCUMENTATION')
    expect(cloned?.values.f1).toBeNull()
    expect(cloned?.values.support).toBeNull()
  })
})

describe('chart values are the table values', () => {
  test('the false-positive chart reads the same numbers as the baseline table', () => {
    // Arrange
    const table = baselineRows(EVALUATION_FIXTURE)

    // Act
    const chart = falsePositiveChartRows(EVALUATION_FIXTURE)

    // Assert
    for (const bar of chart) {
      const row = table.find((entry) => entry.key === bar.key)
      expect(bar.value).toBe(row?.values.false_positives_per_100_clean)
    }
  })

  test('the precision chart reads the same numbers as the baseline table', () => {
    const table = baselineRows(EVALUATION_FIXTURE)

    for (const bar of precisionAtBudgetChartRows(EVALUATION_FIXTURE)) {
      const row = table.find((entry) => entry.key === bar.key)
      expect(bar.value).toBe(row?.values.precision_at_k)
    }
  })

  test('both render through one formatter, so they cannot disagree by a rounding step', () => {
    const hybridBar = falsePositiveChartRows(EVALUATION_FIXTURE).find(
      (bar) => bar.key === 'HYBRID',
    )
    const hybridRow = baselineRows(EVALUATION_FIXTURE).find((row) => row.key === 'HYBRID')

    expect(formatMetric(hybridBar?.value ?? null)).toBe(
      formatMetric(hybridRow?.values.false_positives_per_100_clean ?? null),
    )
    expect(formatMetric(52.5)).toBe('52.5000')
  })

  test('an unmeasured value formats as null, never as a zero string', () => {
    expect(formatMetric(null)).toBeNull()
    expect(formatMetric(0)).toBe('0.0000')
  })
})

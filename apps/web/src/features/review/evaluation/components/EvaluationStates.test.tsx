import { screen } from '@testing-library/react'
import { describe, expect, test, vi } from 'vitest'

import {
  EvaluationFailed,
  EvaluationLoading,
  NoEvaluationRun,
  RUN_COMMAND,
} from '@/features/review/evaluation/components/EvaluationPlaceholders'
import { MetricBarChart } from '@/features/review/evaluation/components/MetricBarChart'
import { MetricTable } from '@/features/review/evaluation/components/MetricTable'
import { baselineRows, BASELINE_COLUMNS } from '@/features/review/evaluation/selectors'
import { EVALUATION_FIXTURE } from '@/features/review/evaluation/test-fixtures'
import { renderWithRouter } from '@/test/render'

/**
 * `sprint/00-app-spec.md` § 6 rule 4: **belum ada evaluasi ≠ nol.**
 *
 * A page of zeros and a page saying nothing has been run look similar and mean opposite things —
 * one claims the evaluation ran and found nothing, the other says no measurement exists. These
 * tests hold that line, and the third state, a service failure, apart from both.
 */
describe('no run yet is distinguishable from a measured zero', () => {
  test('the no-run state shows the command and no metric at all', () => {
    // Arrange & Act
    renderWithRouter(<NoEvaluationRun />)

    // Assert
    expect(screen.getByText('Belum ada evaluasi yang dijalankan')).toBeInTheDocument()
    expect(screen.getByText(RUN_COMMAND)).toBeInTheDocument()
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
    expect(screen.queryByText('0.0000')).not.toBeInTheDocument()
  })

  test('a genuine zero renders as a number, not as an absence', () => {
    const zeroed = [
      {
        key: 'HYBRID',
        label: 'TilikKlaim (hibrida)',
        values: { macro_f1: 0, pr_auc: 0, precision_at_k: 0, recall_at_k: 0,
                  false_positives_per_100_clean: 0 },
      },
    ]

    renderWithRouter(
      <MetricTable caption="c" columns={BASELINE_COLUMNS} rows={zeroed} />,
    )

    expect(screen.getAllByText('0.0000').length).toBe(BASELINE_COLUMNS.length)
    expect(screen.queryByText('Tidak terukur')).not.toBeInTheDocument()
  })

  test('an unmeasured value says so instead of showing a zero', () => {
    renderWithRouter(
      <MetricTable
        caption="c"
        columns={BASELINE_COLUMNS}
        rows={baselineRows(EVALUATION_FIXTURE)}
      />,
    )

    // B0_RANDOM is absent from the fixture, so its whole row is unmeasured.
    expect(screen.getAllByText('Tidak terukur').length).toBe(BASELINE_COLUMNS.length)
  })

  test('a service failure offers a retry and never claims there is no run', () => {
    const onRetry = vi.fn()
    renderWithRouter(<EvaluationFailed onRetry={onRetry} />)

    expect(screen.getByText('Hasil evaluasi tidak dapat dimuat')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Coba lagi/ })).toBeInTheDocument()
    expect(screen.queryByText('Belum ada evaluasi yang dijalankan')).not.toBeInTheDocument()
  })

  test('loading announces itself rather than showing an empty page', () => {
    renderWithRouter(<EvaluationLoading />)

    expect(screen.getByText('Memuat hasil evaluasi…')).toBeInTheDocument()
  })
})

describe('a chart never draws an unmeasured value as a bar', () => {
  test('an unmeasured row is labelled, not drawn at zero length', () => {
    renderWithRouter(
      <MetricBarChart
        title="t"
        subtitle="s"
        rows={[
          { key: 'HYBRID', label: 'Hibrida', value: 52.5 },
          { key: 'B0_RANDOM', label: 'Acak', value: null },
        ]}
      />,
    )

    expect(screen.getByText('52.5000')).toBeInTheDocument()
    expect(screen.getByText('Tidak terukur')).toBeInTheDocument()
    expect(screen.queryByText('0.0000')).not.toBeInTheDocument()
  })
})

import { LatencyCard } from '@/features/review/evaluation/components/LatencyCard'
import { LimitationsCard } from '@/features/review/evaluation/components/LimitationsCard'
import { MetricBarChart } from '@/features/review/evaluation/components/MetricBarChart'
import { MetricTable } from '@/features/review/evaluation/components/MetricTable'
import { SyntheticBadge } from '@/features/review/evaluation/components/SyntheticBadge'
import { VersionCard } from '@/features/review/evaluation/components/VersionCard'
import {
  EvaluationFailed,
  EvaluationLoading,
  NoEvaluationRun,
} from '@/features/review/evaluation/components/EvaluationPlaceholders'
import {
  baselineColumns,
  baselineRows,
  modeColumns,
  falsePositiveChartRows,
  modeRows,
  precisionAtBudgetChartRows,
} from '@/features/review/evaluation/selectors'
import { useEvaluation } from '@/features/review/evaluation/useEvaluation'
import { useDocumentTitle } from '@/modules/document-title/useDocumentTitle'
import { useTranslation } from 'react-i18next'
import { PageHeader, PageShell } from '@/components/layouts/PageShell'

/**
 * Page 4 — Audit & evaluation (`/evaluation`). Widgets 1–9 per `sprint/00-app-spec.md` § 6.
 *
 * **Display only.** There is no threshold control, no what-if input, and no button that starts a
 * run — rule 1, and it is a safety property rather than a scope cut. A page that could re-tune a
 * threshold would let someone tune against the frozen test set, which invalidates every number
 * the same page is showing.
 *
 * The limitations card renders inside the same branch as the metrics, so no code path can show a
 * number without it (rule 3).
 */
export function EvaluationPage() {
  const { t } = useTranslation('evaluation')

  useDocumentTitle(t('page.title'))
  const { status, data, reload } = useEvaluation()

  return (
    <PageShell>
      <PageHeader
        eyebrow={t('page.eyebrow')}
        title={t('page.title')}
        lede={t('page.lede')}
      />

      <div className="space-y-4">
        {status === 'loading' ? <EvaluationLoading /> : null}
        {status === 'absent' ? <NoEvaluationRun /> : null}
        {status === 'failed' ? <EvaluationFailed onRetry={reload} /> : null}

        {status === 'ready' && data ? (
          <>
            <SyntheticBadge dataClass={data.data_class} />
            <VersionCard evaluation={data} />

            <section
              aria-labelledby="baselines-heading"
              className="rounded-md border border-line bg-card p-4"
            >
              <h2 id="baselines-heading" className="mb-1 text-lead font-semibold text-ink">
                {t('page.baselinesHeading')}
              </h2>
              <p className="mb-3 text-micro text-ink-2">{t('page.baselinesBody')}</p>
              <MetricTable
                caption={t('page.baselinesCaption')}
                columns={baselineColumns()}
                rows={baselineRows(data)}
              />
            </section>

            <section
              aria-labelledby="per-mode-heading"
              className="rounded-md border border-line bg-card p-4"
            >
              <h2 id="per-mode-heading" className="mb-1 text-lead font-semibold text-ink">
                {t('page.perModeHeading')}
              </h2>
              <p className="mb-3 text-micro text-ink-2">{t('page.perModeBody')}</p>
              <MetricTable
                caption={t('page.perModeCaption')}
                columns={modeColumns()}
                rows={modeRows(data)}
              />
            </section>

            <div className="grid gap-4 lg:grid-cols-2">
              <MetricBarChart
                title={t('page.falsePositiveTitle')}
                subtitle={t('page.falsePositiveSubtitle')}
                rows={falsePositiveChartRows(data)}
              />
              <MetricBarChart
                title={t('page.precisionTitle')}
                subtitle={t('page.precisionSubtitle')}
                rows={precisionAtBudgetChartRows(data)}
              />
            </div>

            <LatencyCard p50={data.latency_p50_ms} p95={data.latency_p95_ms} />
            <LimitationsCard limitations={data.limitations} />
          </>
        ) : null}
      </div>
    </PageShell>
  )
}

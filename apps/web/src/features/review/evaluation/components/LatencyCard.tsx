import { Trans, useTranslation } from 'react-i18next'

import { formatLatency } from '@/features/review/evaluation/format'

/** The artifact holding the unrounded figures. Named once so copy and repo cannot disagree. */
const LATENCY_FILE = 'latency.json'

/**
 * Widget 7 — screening latency.
 *
 * Labelled as a prototype measurement, because that is what it is. `docs/canonical/06_evaluation_plan.md`
 * lists latency under "demonstrates prototype latency and workflow can be measured" and under
 * "does not demonstrate scale under national production load"; showing the number without that
 * distinction invites the second reading, and it invites it in either language.
 */
export function LatencyCard({
  p50,
  p95,
}: {
  readonly p50: number
  readonly p95: number
}) {
  const { t } = useTranslation('evaluation')

  return (
    <section
      aria-labelledby="latency-heading"
      className="rounded-md border border-line bg-card p-4"
    >
      <h3 id="latency-heading" className="text-body-lg font-semibold text-ink">
        {t('latency.heading')}
      </h3>
      <p className="mb-3 text-micro text-ink-2">
        <Trans
          i18nKey="latency.body"
          ns="evaluation"
          values={{ file: LATENCY_FILE }}
          components={[<span key="0" />, <code key="1" className="font-mono" />]}
        />
      </p>
      <dl className="flex gap-8">
        <div>
          <dt className="text-micro text-ink-2">{t('latency.median')}</dt>
          <dd className="font-mono text-lead tabular-nums text-ink">{formatLatency(p50)}</dd>
        </div>
        <div>
          <dt className="text-micro text-ink-2">{t('latency.p95')}</dt>
          <dd className="font-mono text-lead tabular-nums text-ink">{formatLatency(p95)}</dd>
        </div>
      </dl>
    </section>
  )
}

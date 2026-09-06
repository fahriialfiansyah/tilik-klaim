import { Trans, useTranslation } from 'react-i18next'

/**
 * Widget 2 — the synthetic-data badge.
 *
 * Prominent by design, and never conditional. Every number on this page was produced from
 * records this project generated; a reader who misses that will read a prevalence into a figure
 * that is a test-design choice. The badge reads the `data_class` the API sent rather than being
 * hardcoded, so it cannot say "synthetic" about a run that claimed otherwise — and any class
 * other than `synthetic` is shown verbatim rather than translated, because a word we do not
 * recognise is not a word we should be rephrasing on a governance marker.
 */
export function SyntheticBadge({ dataClass }: { readonly dataClass: string }) {
  const { t } = useTranslation('evaluation')
  const shown =
    dataClass === 'synthetic' ? t('synthetic.syntheticWord') : dataClass

  return (
    <p
      className="mb-4 rounded-md border border-notice-line bg-notice-bg px-4 py-3 text-body-lg text-ink"
      role="note"
    >
      <span className="mr-2 rounded-sm bg-ink px-2 py-[2px] text-micro font-semibold uppercase tracking-wide text-card">
        {t('synthetic.badge', { dataClass: shown })}
      </span>
      <Trans
        i18nKey="synthetic.body"
        ns="evaluation"
        components={[<span key="0" />, <strong key="1" />]}
      />
    </p>
  )
}

import { Trans, useTranslation } from 'react-i18next'

import type { EvaluationResponse } from '@/features/review/evaluation/types'
import { formatDateTime } from '@/features/review/shared/format'

/** The artifact holding the threshold formulation. Named once. */
const MANIFEST_FILE = 'manifest.json'

/**
 * Widget 1 — the version card.
 *
 * The manifest's own `threshold_logic` string is **not** rendered here. It is a technical
 * artifact field with fixed wording, like the data card and the model card. The page states
 * where the thresholds come from in the reader's language and points at the artifact for the
 * exact formulation, rather than pasting an untranslatable sentence into the screen.
 *
 * A metric without its versions cannot be defended when someone asks how it was produced, so
 * the dataset digest, the generator, the ruleset, the feature set, and the commit all travel
 * with the result rather than living in a separate document that drifts.
 *
 * `code_commit` carries a `-dirty` suffix when the tree had uncommitted changes. That is
 * displayed, not hidden: an unmarked commit on a dirty tree names a state that does not
 * describe the code that ran.
 */
export function VersionCard({ evaluation }: { readonly evaluation: EvaluationResponse }) {
  const { t } = useTranslation('evaluation')
  const { manifest, versions } = evaluation
  const rows: readonly (readonly [string, string])[] = [
    [t('version.run'), evaluation.run_id],
    [t('version.completed'), formatDateTime(evaluation.completed_at)],
    [t('version.datasetHash'), manifest.dataset_hash],
    [t('version.generator'), manifest.generator_version],
    [t('version.ruleset'), versions.ruleset_version],
    [t('version.engine'), versions.engine_version],
    [t('version.feature'), manifest.feature_version],
    [t('version.model'), manifest.model_version],
    [t('version.commit'), manifest.code_commit],
    [t('version.environment'), manifest.environment_hash],
  ]

  return (
    <section
      aria-labelledby="version-card-heading"
      className="rounded-md border border-line bg-card p-4"
    >
      <h2 id="version-card-heading" className="mb-3 text-lead font-semibold">
        {t('version.heading')}
      </h2>
      <dl className="grid grid-cols-1 gap-x-6 gap-y-2 sm:grid-cols-2">
        {rows.map(([label, value]) => (
          <div key={label} className="flex justify-between gap-3 border-b border-line py-1">
            <dt className="text-small text-ink-2">{label}</dt>
            <dd className="text-small font-mono text-ink break-all text-right">{value}</dd>
          </div>
        ))}
      </dl>
      <p className="mt-3 text-micro text-ink-2">
        <Trans
          i18nKey="version.thresholds"
          ns="evaluation"
          values={{ file: MANIFEST_FILE }}
          components={[<span key="0" />, <code key="1" className="mx-1 font-mono" />]}
        />
      </p>
    </section>
  )
}

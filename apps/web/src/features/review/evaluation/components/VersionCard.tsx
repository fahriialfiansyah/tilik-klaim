import type { EvaluationResponse } from '@/features/review/evaluation/types'

/**
 * Widget 1 — the version card.
 *
 * The manifest's own `threshold_logic` string is **not** rendered here. It is a technical
 * artifact field and is written in English, like the data card and the model card; this page is
 * read in Indonesian. The page states where the thresholds come from in working language and
 * points at the artifact for the exact wording, rather than pasting an English sentence into an
 * Indonesian screen.
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
  const { manifest, versions } = evaluation
  const rows: readonly (readonly [string, string])[] = [
    ['Run', evaluation.run_id],
    ['Selesai', new Date(evaluation.completed_at).toLocaleString('id-ID')],
    ['Sidik kumpulan data', manifest.dataset_hash],
    ['Versi generator', manifest.generator_version],
    ['Versi aturan', versions.ruleset_version],
    ['Versi mesin', versions.engine_version],
    ['Versi fitur', manifest.feature_version],
    ['Versi model', manifest.model_version],
    ['Commit kode', manifest.code_commit],
    ['Sidik lingkungan', manifest.environment_hash],
  ]

  return (
    <section
      aria-labelledby="version-card-heading"
      className="rounded-md border border-line bg-card p-4"
    >
      <h2 id="version-card-heading" className="mb-3 text-lead font-semibold">
        Penanda versi
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
        Ambang batas pita ditetapkan dari kuantil distribusi skor pada partisi validasi saja,
        tidak pernah dari partisi latih maupun uji. Rumusan teknisnya tercatat pada
        <code className="mx-1 font-mono">manifest.json</code> milik run ini.
      </p>
    </section>
  )
}

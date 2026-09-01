import { Copy } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { MANDATORY_STATEMENT_ID, toWorkingLanguage } from '@/features/review/evaluation/labels'
import type { LimitationsCard as LimitationsCardData } from '@/features/review/evaluation/types'

const COPIED_MS = 2000

/**
 * Widget 8 — the limitations card, copy-ready.
 *
 * `sprint/00-app-spec.md` § 6 rule 3 makes this mandatory whenever a metric is shown, without
 * exception and explicitly including when time is short. It is rendered by `EvaluationPage`
 * inside the same branch as the metrics, so there is no code path that shows one without the
 * other.
 *
 * Copyable because the alternative is somebody retyping it into the deck, and a retyped
 * limitation is a limitation that quietly loses a clause.
 *
 * The canonical rows are stated in English in `docs/canonical/06_evaluation_plan.md` and the
 * artifact carries them verbatim. The page shows the Indonesian rendering, and keeps the
 * mandatory sentence in both — the canonical data card requires that exact sentence, and a
 * reader here needs it in the language they are reading.
 */
export function LimitationsCard({ limitations }: { readonly limitations: LimitationsCardData }) {
  const [copied, setCopied] = useState(false)

  const demonstrates = limitations.demonstrates.map(toWorkingLanguage)
  const doesNotDemonstrate = limitations.does_not_demonstrate.map(toWorkingLanguage)

  const asText = [
    MANDATORY_STATEMENT_ID,
    limitations.mandatory_statement,
    '',
    'Yang ditunjukkan:',
    ...demonstrates.map((line) => `- ${line}`),
    '',
    'Yang tidak ditunjukkan:',
    ...doesNotDemonstrate.map((line) => `- ${line}`),
  ].join('\n')

  const copy = () => {
    void navigator.clipboard?.writeText(asText).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), COPIED_MS)
    })
  }

  return (
    <section
      aria-labelledby="limitations-heading"
      className="rounded-md border border-notice-line bg-notice-bg p-4"
    >
      <div className="mb-3 flex items-start justify-between gap-3">
        <h2 id="limitations-heading" className="text-lead font-semibold text-ink">
          Keterbatasan
        </h2>
        <Button variant="outline" size="sm" onClick={copy}>
          <Copy aria-hidden="true" className="mr-1 h-3 w-3" />
          {copied ? 'Tersalin' : 'Salin'}
        </Button>
      </div>

      <p className="mb-1 text-body-lg text-ink">{MANDATORY_STATEMENT_ID}</p>
      <p className="mb-4 text-micro text-ink-2 italic">{limitations.mandatory_statement}</p>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <h3 className="mb-1 text-small font-semibold text-ink">Yang ditunjukkan</h3>
          <ul className="list-disc space-y-1 pl-5 text-small text-ink-2">
            {demonstrates.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        </div>
        <div>
          <h3 className="mb-1 text-small font-semibold text-ink">Yang tidak ditunjukkan</h3>
          <ul className="list-disc space-y-1 pl-5 text-small text-ink-2">
            {doesNotDemonstrate.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  )
}

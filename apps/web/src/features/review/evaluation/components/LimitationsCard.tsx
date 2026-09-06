import { Copy } from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'

import { copyText } from '@/lib/clipboard'
import { Button } from '@/components/ui/button'
import { toReadable } from '@/features/review/evaluation/labels'
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
 * artifact carries them verbatim. The page renders them in the reader's language, and keeps the
 * artifact's own `mandatory_statement` beside the translated one — the canonical data card
 * requires that exact sentence, and a reader needs it in the language they are reading. In
 * English the two now match word for word, which is the point rather than a coincidence.
 */
export function LimitationsCard({ limitations }: { readonly limitations: LimitationsCardData }) {
  const { t } = useTranslation('evaluation')
  const [copied, setCopied] = useState(false)

  const demonstrates = limitations.demonstrates.map(toReadable)
  const doesNotDemonstrate = limitations.does_not_demonstrate.map(toReadable)
  const mandatory = t('mandatoryStatement')

  const asText = [
    mandatory,
    limitations.mandatory_statement,
    '',
    t('limitations.demonstratesColon'),
    ...demonstrates.map((line) => `- ${line}`),
    '',
    t('limitations.doesNotColon'),
    ...doesNotDemonstrate.map((line) => `- ${line}`),
  ].join('\n')

  const copy = async () => {
    // Only ever reports a copy that actually happened; the clipboard API is absent entirely
    // outside a secure context, which is how this app is usually demonstrated.
    if (await copyText(asText)) {
      setCopied(true)
      setTimeout(() => setCopied(false), COPIED_MS)
    }
  }

  return (
    <section
      aria-labelledby="limitations-heading"
      className="rounded-md border border-notice-line bg-notice-bg p-4"
    >
      <div className="mb-3 flex items-start justify-between gap-3">
        <h2 id="limitations-heading" className="text-lead font-semibold text-ink">
          {t('limitations.heading')}
        </h2>
        <Button variant="outline" size="sm" onClick={() => void copy()}>
          <Copy aria-hidden="true" className="mr-1 h-3 w-3" />
          {copied ? t('limitations.copied') : t('limitations.copy')}
        </Button>
      </div>

      <p className="mb-1 text-body-lg text-ink">{mandatory}</p>
      <p className="mb-4 text-micro text-ink-2 italic">{limitations.mandatory_statement}</p>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <h3 className="mb-1 text-small font-semibold text-ink">
            {t('limitations.demonstrates')}
          </h3>
          <ul className="list-disc space-y-1 pl-5 text-small text-ink-2">
            {demonstrates.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        </div>
        <div>
          <h3 className="mb-1 text-small font-semibold text-ink">
            {t('limitations.doesNot')}
          </h3>
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

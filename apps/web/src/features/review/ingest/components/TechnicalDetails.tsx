import { useTranslation } from 'react-i18next'

import { Button } from '@/components/ui/button'
import { CopyStateIcon } from '@/modules/clipboard/CopyStateIcon'
import { useCopyState } from '@/modules/clipboard/useCopyState'

/**
 * The engineer-facing half of a refusal, folded away.
 *
 * A stable code and the service's own sentence are what a ticket needs, and they are written
 * for someone reading a log: `BUNDLE_SCHEMA_INVALID` names nothing a reviewer can act on, and
 * the service's `detail` arrives in English whatever language the interface is in. Neither
 * belongs in the first thing a reviewer reads — but deleting them would leave a support request
 * with nothing to quote, so they stay one click away and travel together on the clipboard.
 */
export function TechnicalDetails({
  code,
  detail,
}: {
  readonly code: string
  readonly detail: string
}) {
  const { t } = useTranslation('ingest')
  const [copyState, copy] = useCopyState()

  const payload = [code, detail].filter((part) => part.length > 0).join('\n')
  if (payload.length === 0) {
    return null
  }

  return (
    <details className="mt-2">
      <summary className="inline-flex cursor-pointer list-none items-center gap-[6px] text-meta text-ink-3 marker:hidden hover:text-ink-2 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand">
        <span aria-hidden>›</span>
        {t('technical.heading')}
      </summary>

      <div className="mt-2 rounded-sm border border-line bg-sunk p-[11px]">
        <div className="flex items-start justify-between gap-3">
          <p data-numeric className="min-w-0 font-mono text-meta break-all text-ink-2">
            {code}
          </p>
          <Button variant="outline" size="sm" className="shrink-0" onClick={() => void copy(payload)}>
            <CopyStateIcon state={copyState} />
            {t(`copy.${copyState}` as 'copy.idle')}
          </Button>
        </div>
        {detail.length > 0 ? (
          <p className="mt-[6px] font-mono text-micro leading-relaxed break-all text-ink-3">
            {detail}
          </p>
        ) : null}
      </div>
    </details>
  )
}

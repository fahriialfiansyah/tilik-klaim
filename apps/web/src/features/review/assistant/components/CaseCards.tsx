import { ArrowUpRight } from 'lucide-react'
import type { CSSProperties } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { shortId } from '@/features/review/assistant/conversation'
import type { CaseCard } from '@/features/review/assistant/types'
import { BAND_RAIL, BandBadge } from '@/features/review/shared/components/BandBadge'
import { useStateLabel } from '@/features/review/shared/labels'
import { cn } from '@/lib/utils'

/**
 * The cases an answer is about, as the queue itself shows them.
 *
 * Every field is the queue row verbatim — reason sentence first, the band as colour **and**
 * text, the position the queue gave it. The assistant adds two navigations and nothing else:
 * narrow the conversation to this case, or open it.
 */
export function CaseCards({
  cards,
  activeCaseId,
  onFocusCase,
}: {
  readonly cards: readonly CaseCard[]
  readonly activeCaseId: string | null
  readonly onFocusCase: (caseId: string) => void
}) {
  const { t } = useTranslation('assistant')
  const stateLabel = useStateLabel()

  return (
    <ul className="space-y-[8px]">
      {cards.map(({ queue_position: position, case: row }, index) => (
        <li
          key={row.case_id}
          className="tk-enter relative flex flex-col gap-3 overflow-hidden rounded-md border border-line bg-card py-[11px] pr-[12px] pl-[15px] sm:flex-row sm:items-center"
          style={{ '--tk-index': index } as CSSProperties}
        >
          <span aria-hidden className={cn('absolute inset-y-0 left-0 w-[3px]', BAND_RAIL[row.band])} />
          <div className="min-w-0 flex-1">
            <p className="flex flex-wrap items-center gap-x-[10px] gap-y-1 text-meta text-ink-3">
              <span data-numeric className="font-mono">
                {t('answer.position', { n: position })}
              </span>
              <span data-numeric title={row.case_id} className="font-mono font-medium text-ink-2">
                {shortId(row.case_id)}
              </span>
              <BandBadge band={row.band} className="px-[7px] py-[1px] text-meta" />
              <span>{stateLabel(row.state)}</span>
            </p>
            <p className="mt-[5px] text-small text-ink text-pretty">{row.reason_sentence}</p>
          </div>
          <div className="flex shrink-0 items-center gap-1">
            {activeCaseId === row.case_id ? null : (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onFocusCase(row.case_id)}
                aria-label={t('answer.focusCaseLabel', { id: shortId(row.case_id) })}
              >
                {t('answer.focusCase')}
              </Button>
            )}
            <Button variant="ghost" size="sm" asChild>
              <Link to={`/cases/${encodeURIComponent(row.case_id)}`}>
                {t('answer.openCase')}
                <ArrowUpRight aria-hidden />
              </Link>
            </Button>
          </div>
        </li>
      ))}
    </ul>
  )
}

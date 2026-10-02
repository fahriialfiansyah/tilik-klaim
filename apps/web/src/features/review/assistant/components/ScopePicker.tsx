import { Check, ChevronDown, FolderOpen, ListOrdered } from 'lucide-react'
import { useRef } from 'react'
import { useTranslation } from 'react-i18next'

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { PerfectScrollArea } from '@/components/wrappers/PerfectScrollArea'
import { shortId } from '@/features/review/assistant/conversation'
import type { AssistantScope } from '@/features/review/assistant/types'
import type { QueueCasesState } from '@/features/review/assistant/useQueueCases'
import { BAND_RAIL } from '@/features/review/shared/components/BandBadge'
import { useBandLabel } from '@/features/review/shared/labels'
import { cn } from '@/lib/utils'

/**
 * What the next question reads: the whole queue, or one case (ADR-0007 § 2).
 *
 * Always visible beside the input, because the same words — "why?", "what is missing?" — mean
 * different things against different scopes, and a reviewer must never have to guess which one
 * an answer was about. Cases are listed in the queue's own order, with its position.
 */
export function ScopePicker({
  scope,
  queue,
  isDisabled,
  onChange,
  onChosen,
}: {
  readonly scope: AssistantScope
  readonly queue: QueueCasesState
  readonly isDisabled: boolean
  readonly onChange: (scope: AssistantScope) => void
  /** Where focus goes after a choice. Without one, Radix returns focus to the trigger. */
  readonly onChosen?: () => void
}) {
  const { t } = useTranslation('assistant')
  const hasChosen = useRef(false)
  const choose = (next: AssistantScope) => {
    hasChosen.current = true
    onChange(next)
  }
  const bandLabel = useBandLabel()
  const current =
    scope.kind === 'CASE' ? t('scope.case', { id: shortId(scope.case_id) }) : t('scope.queue')
  const TriggerIcon = scope.kind === 'CASE' ? FolderOpen : ListOrdered

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        disabled={isDisabled}
        aria-label={t('scope.change', { current })}
        className="inline-flex h-8 max-w-full items-center gap-[7px] rounded-full border border-line bg-sunk px-[11px] text-small text-ink-2 transition-colors hover:border-brand-line hover:text-brand focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand disabled:pointer-events-none disabled:opacity-50 data-[state=open]:border-brand-line data-[state=open]:text-brand"
      >
        <span className="font-mono text-micro font-semibold tracking-label text-ink-3">
          {t('scope.label').toUpperCase()}
        </span>
        <TriggerIcon aria-hidden className="size-[14px] shrink-0" />
        <span data-numeric className="truncate font-medium">
          {current}
        </span>
        <ChevronDown aria-hidden className="size-[14px] shrink-0" />
      </DropdownMenuTrigger>

      <DropdownMenuContent
        align="start"
        side="top"
        aria-label={t('scope.menuLabel')}
        className="w-[min(420px,calc(100vw-32px))] p-0"
        onCloseAutoFocus={(event) => {
          if (hasChosen.current && onChosen) {
            event.preventDefault()
            onChosen()
          }
          hasChosen.current = false
        }}
      >
        <div className="p-1">
          <DropdownMenuItem onSelect={() => choose({ kind: 'QUEUE' })} className="items-start">
            <ListOrdered aria-hidden className="mt-[3px] size-[15px] shrink-0 text-ink-3" />
            <span className="min-w-0 flex-1">
              <span className="block font-medium">{t('scope.queueOption')}</span>
              <span className="block text-meta text-ink-3">{t('scope.queueOptionHint')}</span>
            </span>
            {scope.kind === 'QUEUE' ? <Check aria-hidden className="mt-[3px] size-[15px] text-brand" /> : null}
          </DropdownMenuItem>
        </div>
        <DropdownMenuSeparator className="my-0" />
        <DropdownMenuLabel className="px-[14px] pt-[10px] pb-[4px] font-mono text-micro font-semibold tracking-label text-ink-3">
          {t('scope.casesHeading')}
        </DropdownMenuLabel>

        {queue.cases.length === 0 ? (
          <p className="px-[14px] pb-[12px] text-meta text-ink-3">
            {queue.status === 'loading'
              ? t('scope.loading')
              : queue.status === 'failed'
                ? t('scope.failed')
                : t('scope.empty')}
          </p>
        ) : (
          <PerfectScrollArea className="max-h-[300px]">
            <div className="p-1 pt-0">
              {queue.cases.map(({ position, row }) => {
                const isActive = scope.kind === 'CASE' && scope.case_id === row.case_id
                return (
                  <DropdownMenuItem
                    key={row.case_id}
                    onSelect={() => choose({ kind: 'CASE', case_id: row.case_id })}
                    className="items-start"
                  >
                    <span aria-hidden className={cn('mt-[2px] h-[30px] w-[3px] shrink-0 rounded-sm', BAND_RAIL[row.band])} />
                    <span className="min-w-0 flex-1">
                      <span className="flex items-center gap-2 text-meta text-ink-3">
                        <span data-numeric className="font-mono">
                          {t('scope.position', { n: position })}
                        </span>
                        <span data-numeric className="font-mono font-medium text-ink">
                          {shortId(row.case_id)}
                        </span>
                        <span className="truncate">{bandLabel(row.band)}</span>
                      </span>
                      <span className="block truncate text-small text-ink-2">{row.reason_sentence}</span>
                    </span>
                    {isActive ? <Check aria-hidden className="mt-[3px] size-[15px] text-brand" /> : null}
                  </DropdownMenuItem>
                )
              })}
            </div>
          </PerfectScrollArea>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

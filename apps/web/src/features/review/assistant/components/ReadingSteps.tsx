import { Check, ChevronRight, LoaderCircle } from 'lucide-react'
import { useTranslation } from 'react-i18next'

import { shortId, type Turn } from '@/features/review/assistant/conversation'
import { toolLabel, usePhaseLabel } from '@/features/review/assistant/labels'
import type { ToolCallRecord } from '@/features/review/case-briefing/types'

/**
 * A step names what it read in words, plus the one argument a reviewer can place: which case.
 * Filter values and reason codes are machine tokens and stay off the reading surface — the
 * step's label already says what kind of read it was.
 */
function Steps({ calls }: { readonly calls: readonly ToolCallRecord[] }) {
  return (
    <>
      {calls.map((call, index) => (
        <li key={`${call.tool}-${index}`} className="flex flex-wrap items-center gap-x-2 text-meta text-ink-2">
          <Check aria-hidden className="size-3 shrink-0 text-ink-3" />
          <span>{toolLabel(call.tool)}</span>
          {call.arguments.case_id ? (
            <span data-numeric title={call.arguments.case_id} className="font-mono text-ink-3">
              {shortId(call.arguments.case_id)}
            </span>
          ) : null}
        </li>
      ))}
    </>
  )
}

/**
 * What the answer read, in order — the transparency artifact ADR-0005 § 6 introduced and
 * ADR-0007 § 6 keeps: the answer to "what did it actually look at".
 *
 * Open while the answer is being prepared, folded once it is ready: by then the sources list
 * says what the answer *cites*, and the reading log is detail for whoever wants it.
 */
export function ReadingSteps({ turn }: { readonly turn: Turn }) {
  const { t } = useTranslation('assistant')
  const phaseLabel = usePhaseLabel()

  if (turn.status === 'streaming') {
    return (
      <ol className="space-y-[5px] rounded-md border border-line bg-sunk px-[12px] py-[9px]">
        <Steps calls={turn.toolCalls} />
        <li className="flex items-center gap-2 text-meta text-ink-2">
          <LoaderCircle aria-hidden className="size-3 shrink-0 animate-spin text-brand" />
          <span>
            {turn.phase ? phaseLabel(turn.phase) : t('turn.reading')}
            {turn.phase === 'READING' && turn.phaseDetail ? (
              <span className="text-ink-3"> · {toolLabel(turn.phaseDetail)}</span>
            ) : null}
          </span>
        </li>
      </ol>
    )
  }

  if (turn.status !== 'done') {
    return null
  }

  if (turn.toolCalls.length === 0) {
    return <p className="text-meta text-ink-3">{t('turn.noSteps')}</p>
  }

  return (
    <details className="group">
      <summary className="inline-flex cursor-pointer list-none items-center gap-[6px] text-meta text-ink-3 marker:hidden hover:text-ink-2 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand">
        <ChevronRight
          aria-hidden
          className="size-[12px] shrink-0 transition-transform duration-[var(--motion-fast)] group-open:rotate-90"
        />
        {t('turn.steps', { count: turn.toolCalls.length })}
      </summary>
      <ol
        aria-label={t('turn.stepsHeading')}
        className="mt-2 space-y-[5px] rounded-md border border-line bg-sunk px-[12px] py-[9px]"
      >
        <Steps calls={turn.toolCalls} />
      </ol>
    </details>
  )
}

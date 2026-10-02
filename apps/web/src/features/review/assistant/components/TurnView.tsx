import { memo } from 'react'
import { useTranslation } from 'react-i18next'

import { AssistantIcon } from '@/components/layouts/MenuIcons'
import { AnswerView, type AnswerActions } from '@/features/review/assistant/components/AnswerView'
import { ReadingSteps } from '@/features/review/assistant/components/ReadingSteps'
import { shortId, type Turn } from '@/features/review/assistant/conversation'
import type { RiskMode } from '@/features/review/shared/types'

/**
 * One exchange: the reviewer's question, then the assistant's answer.
 *
 * The question carries the scope it was asked in, because the same words mean different things
 * against the whole queue and against one case — and a reader scrolling back must be able to tell
 * which one an old answer was about.
 */
export const TurnView = memo(function TurnView({
  turn,
  isLatest,
  isBusy,
  modes,
  actions,
}: {
  readonly turn: Turn
  readonly isLatest: boolean
  readonly isBusy: boolean
  readonly modes: readonly RiskMode[]
  readonly actions: AnswerActions
}) {
  const { t } = useTranslation('assistant')
  const scopeLabel =
    turn.scope.kind === 'CASE'
      ? t('turn.scopeCase', { id: shortId(turn.scope.case_id) })
      : t('turn.scopeQueue')

  return (
    <article data-turn aria-label={turn.question} className="space-y-[14px]">
      <div className="flex flex-col items-end gap-[5px]">
        <p className="sr-only">{t('turn.you')}</p>
        <p className="max-w-[min(560px,85%)] rounded-lg rounded-br-sm border border-brand-line bg-brand-soft px-[14px] py-[9px] text-body-lg text-ink text-pretty whitespace-pre-wrap">
          {turn.question}
        </p>
        <p data-numeric className="font-mono text-micro text-ink-3">{scopeLabel}</p>
      </div>

      <div className="flex gap-[12px]">
        <span
          aria-hidden
          className="mt-[2px] flex size-[30px] shrink-0 items-center justify-center rounded-md border border-brand-line bg-brand-soft text-brand"
        >
          <AssistantIcon className="size-[17px]" />
        </span>
        <div className="min-w-0 flex-1">
          <p className="mb-[8px] text-small font-semibold text-ink">{t('turn.assistant')}</p>
          <div className="mb-[12px]">
            <ReadingSteps turn={turn} />
          </div>
          <AnswerView turn={turn} isLatest={isLatest} isBusy={isBusy} modes={modes} actions={actions} />
        </div>
      </div>
    </article>
  )
})

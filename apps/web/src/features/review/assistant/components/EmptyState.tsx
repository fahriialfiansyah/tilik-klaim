import {
  ArrowDownWideNarrow,
  Clock,
  Columns2,
  FileSearch,
  Layers,
  ListChecks,
  ListFilter,
  Scale,
  SearchCheck,
  type LucideIcon,
} from 'lucide-react'
import type { CSSProperties } from 'react'
import { useTranslation } from 'react-i18next'

import { AssistantIcon } from '@/components/layouts/MenuIcons'
import { shortId } from '@/features/review/assistant/conversation'
import type { Suggestion } from '@/features/review/assistant/labels'
import type { AssistantScope } from '@/features/review/assistant/types'

/** One drawn hint per suggestion, from the icon vocabulary DESIGN.md allows — evidence, time, lists. */
const ICONS: Readonly<Record<string, LucideIcon>> = {
  QUEUE_OVERVIEW: ListChecks,
  WHERE_TO_START: ArrowDownWideNarrow,
  CASES_MATCHING: ListFilter,
  CONFLICTS: Layers,
  WHY_RAISED: SearchCheck,
  MISSING_EVIDENCE: FileSearch,
  COUNTER_EVIDENCE: Scale,
  TIMELINE: Clock,
  COMPARISON: Columns2,
}

/**
 * The page before anything has been asked.
 *
 * It says what the assistant reads and offers the questions it is best at, for the scope the
 * reviewer is in. It does not greet, does not promise, and has no mascot: the drawn mark is the
 * menu's own, a balloon with a citation bracket in it.
 */
export function EmptyState({
  scope,
  suggestions,
  isDisabled,
  onPick,
}: {
  readonly scope: AssistantScope
  readonly suggestions: readonly Suggestion[]
  readonly isDisabled: boolean
  readonly onPick: (question: string) => void
}) {
  const { t } = useTranslation('assistant')
  const heading =
    scope.kind === 'CASE'
      ? t('empty.caseHeading', { id: shortId(scope.case_id) })
      : t('empty.queueHeading')

  return (
    <div className="my-auto w-full py-[28px]">
      <div className="mb-[26px] flex flex-col items-center text-center">
        <span
          aria-hidden
          className="mb-[16px] flex size-[48px] items-center justify-center rounded-lg border border-brand-line bg-brand-soft text-brand"
        >
          <AssistantIcon className="size-[26px]" />
        </span>
        <h2 className="mb-[6px] text-title font-semibold tracking-title text-ink">{t('empty.heading')}</h2>
        <p className="max-w-[500px] text-body-lg text-ink-2 text-pretty">{t('empty.body')}</p>
      </div>

      <p className="mb-[9px] font-mono text-micro font-semibold tracking-label text-ink-3">{heading}</p>
      <ul className="grid gap-[8px] sm:grid-cols-2">
        {suggestions.map((suggestion, index) => {
          const Icon = ICONS[suggestion.key] ?? ListChecks
          return (
            <li
              key={suggestion.key}
              className="tk-enter"
              style={{ '--tk-index': index } as CSSProperties}
            >
              <button
                type="button"
                disabled={isDisabled}
                onClick={() => onPick(suggestion.question)}
                className="group flex h-full w-full items-start gap-[11px] rounded-lg border border-line bg-card px-[14px] py-[12px] text-left shadow-panel transition-colors duration-[var(--motion-fast)] hover:border-brand-line hover:bg-brand-soft disabled:pointer-events-none disabled:opacity-50"
              >
                <Icon
                  aria-hidden
                  className="mt-[2px] size-[16px] shrink-0 text-ink-3 transition-colors group-hover:text-brand"
                />
                <span className="text-body text-ink group-hover:text-brand">{suggestion.question}</span>
              </button>
            </li>
          )
        })}
      </ul>
    </div>
  )
}

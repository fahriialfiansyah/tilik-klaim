import { Info, RotateCw } from 'lucide-react'
import type { CSSProperties, ReactNode } from 'react'
import { useTranslation } from 'react-i18next'

import { Button } from '@/components/ui/button'
import { CaseCards } from '@/features/review/assistant/components/CaseCards'
import { CitationChip, SourceList } from '@/features/review/assistant/components/Citations'
import { SuggestionChips } from '@/features/review/assistant/components/SuggestionChips'
import {
  answerAsText,
  citationKey,
  numberedSources,
  type Turn,
} from '@/features/review/assistant/conversation'
import {
  useFailureMessage,
  useGeneratedByLabel,
  useSuggestions,
} from '@/features/review/assistant/labels'
import type { AssistantAnswer, Citation } from '@/features/review/assistant/types'
import { TechnicalDetails } from '@/features/review/ingest/components/TechnicalDetails'
import type { RiskMode } from '@/features/review/shared/types'
import { CopyStateIcon } from '@/modules/clipboard/CopyStateIcon'
import { useCopyState } from '@/modules/clipboard/useCopyState'

const MICRO_LABEL = 'mb-[7px] font-mono text-micro font-semibold tracking-label text-ink-3'

export type AnswerActions = {
  readonly onOpenResource: (citation: Citation) => void
  readonly onFocusCase: (caseId: string) => void
  /** Ask in the page's current scope — suggestion chips. */
  readonly onAsk: (question: string) => void
  /** Ask a turn's question again **in that turn's own scope**, whatever the page shows now. */
  readonly onRetry: (turn: Turn) => void
}

function Section({ label, children }: { readonly label: string; readonly children: ReactNode }) {
  return (
    <section aria-label={label} className="mt-[18px]">
      <p className={MICRO_LABEL}>{label}</p>
      {children}
    </section>
  )
}

/** Statements, each followed by the numbers of what it cites. Reason first, provenance last. */
function Statements({
  answer,
  onOpenResource,
}: {
  readonly answer: AssistantAnswer
  readonly onOpenResource: (citation: Citation) => void
}) {
  const { numberOf } = numberedSources(answer)
  return (
    <div className="space-y-[10px]">
      {answer.statements.map((statement, index) => (
        <p
          key={`${index}:${statement.text}`}
          className="tk-enter text-body-lg leading-relaxed text-ink text-pretty"
          style={{ '--tk-index': index } as CSSProperties}
        >
          {statement.text}{' '}
          <span className="whitespace-nowrap">
            {statement.citations.map((citation) => (
              <CitationChip
                key={citationKey(citation)}
                number={numberOf(citation)}
                citation={citation}
                onOpenResource={onOpenResource}
              />
            ))}
          </span>
        </p>
      ))}
    </div>
  )
}

/** How the answer was made — stated after it, never as a badge over it (ADR-0007 § 6). */
function Provenance({ turn, answer }: { readonly turn: Turn; readonly answer: AssistantAnswer }) {
  const { t } = useTranslation('assistant')
  const generatedByLabel = useGeneratedByLabel()
  return (
    <Section label={t('answer.howMade')}>
      <p data-numeric className="text-meta text-ink-3">
        {generatedByLabel(answer.generated_by)}
        {answer.model_id ? ` · ${answer.model_id}` : ''}
        {t('answer.ruleset', { version: answer.versions.ruleset_version })}
        {turn.viaFallback ? t('answer.viaFallback') : ''}
      </p>
      {answer.validation_rejected ? (
        <>
          <p className="mt-1 text-meta text-ink-2 text-pretty">{t('answer.rejected')}</p>
          <TechnicalDetails code="ASSISTANT_VALIDATION" detail={answer.rejection_reason ?? ''} />
        </>
      ) : null}
    </Section>
  )
}

/** A refusal or "not recognised": the reason in plain words, then where to go instead. */
function Notice({
  answer,
  isLatest,
  isBusy,
  modes,
  onAsk,
}: {
  readonly answer: AssistantAnswer
  readonly isLatest: boolean
  readonly isBusy: boolean
  readonly modes: readonly RiskMode[]
  readonly onAsk: (question: string) => void
}) {
  const { t } = useTranslation('assistant')
  const suggestions = useSuggestions()
  const isRefusal = answer.kind === 'REFUSAL'
  return (
    <div className="rounded-md border border-line bg-sunk px-[14px] py-[12px]">
      <p className="mb-[5px] flex items-center gap-2 text-small font-semibold text-ink">
        <Info aria-hidden className="size-[15px] shrink-0 text-ink-3" />
        {isRefusal ? t('answer.refusalHeading') : t('answer.helpHeading')}
      </p>
      <p className="text-body text-ink-2 text-pretty">{answer.notice}</p>
      {isLatest ? (
        <div className="mt-[12px]">
          <SuggestionChips
            heading={t('answer.followUps')}
            suggestions={suggestions(answer.scope.kind, { modes })}
            isDisabled={isBusy}
            onPick={onAsk}
          />
        </div>
      ) : null}
    </div>
  )
}

function Failure({
  turn,
  isBusy,
  onRetry,
}: {
  readonly turn: Turn
  readonly isBusy: boolean
  readonly onRetry: (turn: Turn) => void
}) {
  const { t } = useTranslation('assistant')
  const failureMessage = useFailureMessage()
  if (!turn.failure) {
    return null
  }
  return (
    <div role="alert" className="rounded-md border border-line bg-sunk px-[14px] py-[12px]">
      <p className="mb-[4px] text-small font-semibold text-ink">{t('failure.heading')}</p>
      <p className="text-body text-ink-2 text-pretty">{failureMessage(turn.failure)}</p>
      <Button
        variant="outline"
        size="sm"
        className="mt-[10px]"
        disabled={isBusy}
        onClick={() => onRetry(turn)}
      >
        <RotateCw aria-hidden />
        {t('failure.retry')}
      </Button>
      <TechnicalDetails code={turn.failure.code ?? 'NETWORK'} detail={turn.failure.detail} />
    </div>
  )
}

function Actions({
  turn,
  answer,
  isBusy,
  onRetry,
}: {
  readonly turn: Turn
  readonly answer: AssistantAnswer
  readonly isBusy: boolean
  readonly onRetry: (turn: Turn) => void
}) {
  const { t } = useTranslation('assistant')
  const [copyState, copy] = useCopyState()
  const text = answerAsText(answer, {
    sources: t('answer.sourcesPlain'),
    uncertainty: t('answer.uncertaintyPlain'),
  })
  return (
    <div className="mt-[14px] flex flex-wrap items-center gap-1">
      <Button variant="ghost" size="sm" aria-label={t('answer.copyLabel')} onClick={() => void copy(text)}>
        <CopyStateIcon state={copyState} />
        {t(`answer.copy.${copyState}` as 'answer.copy.idle')}
      </Button>
      <Button variant="ghost" size="sm" disabled={isBusy} onClick={() => onRetry(turn)}>
        <RotateCw aria-hidden />
        {t('answer.retry')}
      </Button>
    </div>
  )
}

/**
 * One answer. Reading order is binding: statements, their sources, the cases they are about,
 * the uncertainty, and only then how it was made. **No control here acts on a case** — the
 * buttons navigate, copy, or ask again (ADR-0007 § 7).
 */
export function AnswerView({
  turn,
  isLatest,
  isBusy,
  modes,
  actions,
}: {
  readonly turn: Turn
  readonly isLatest: boolean
  readonly isBusy: boolean
  /** The scoped case's risk modes, so follow-ups never offer a comparison it cannot have. */
  readonly modes: readonly RiskMode[]
  readonly actions: AnswerActions
}) {
  const { t } = useTranslation('assistant')
  const suggestions = useSuggestions()
  const answer = turn.answer

  if (turn.status === 'failed') {
    return <Failure turn={turn} isBusy={isBusy} onRetry={actions.onRetry} />
  }
  if (turn.status === 'stopped') {
    return <p className="text-small text-ink-3">{t('turn.stopped')}</p>
  }
  if (!answer) {
    return (
      <div aria-hidden className="space-y-[9px] pt-1">
        <span className="block h-[12px] w-[92%] animate-pulse rounded-sm bg-line" />
        <span className="block h-[12px] w-[78%] animate-pulse rounded-sm bg-line" />
        <span className="block h-[12px] w-[60%] animate-pulse rounded-sm bg-line" />
      </div>
    )
  }
  if (answer.kind !== 'ANSWER') {
    return (
      <Notice
        answer={answer}
        isLatest={isLatest}
        isBusy={isBusy}
        modes={modes}
        onAsk={actions.onAsk}
      />
    )
  }

  const { sources } = numberedSources(answer)
  const activeCaseId = answer.scope.kind === 'CASE' ? answer.scope.case_id : null
  return (
    <div>
      <Statements answer={answer} onOpenResource={actions.onOpenResource} />

      <Section label={t('answer.sources')}>
        <SourceList sources={sources} onOpenResource={actions.onOpenResource} />
      </Section>

      {answer.cases.length > 0 ? (
        <Section label={t('answer.cases')}>
          <CaseCards cards={answer.cases} activeCaseId={activeCaseId} onFocusCase={actions.onFocusCase} />
        </Section>
      ) : null}

      <Section label={t('answer.uncertainty')}>
        <p className="text-small text-ink-2 text-pretty">{answer.uncertainty_note}</p>
      </Section>

      <Provenance turn={turn} answer={answer} />

      <Actions turn={turn} answer={answer} isBusy={isBusy} onRetry={actions.onRetry} />

      {isLatest ? (
        <div className="mt-[14px]">
          <SuggestionChips
            heading={t('answer.followUps')}
            suggestions={suggestions(answer.scope.kind, { exclude: answer.intent, modes })}
            isDisabled={isBusy}
            onPick={actions.onAsk}
          />
        </div>
      ) : null}
    </div>
  )
}

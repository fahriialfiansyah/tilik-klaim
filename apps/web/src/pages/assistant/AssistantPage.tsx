import { SquarePen } from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { useSearchParams } from 'react-router-dom'

import { PageHeader, PageShell } from '@/components/layouts/PageShell'
import { Button } from '@/components/ui/button'
import { PerfectScrollArea } from '@/components/wrappers/PerfectScrollArea'
import type { AnswerActions } from '@/features/review/assistant/components/AnswerView'
import { Composer } from '@/features/review/assistant/components/Composer'
import { ContextPanel } from '@/features/review/assistant/components/ContextPanel'
import { EmptyState } from '@/features/review/assistant/components/EmptyState'
import { TurnView } from '@/features/review/assistant/components/TurnView'
import type { Turn } from '@/features/review/assistant/conversation'
import { useSuggestions } from '@/features/review/assistant/labels'
import { QUEUE_SCOPE, type AssistantScope } from '@/features/review/assistant/types'
import { useAskAssistant } from '@/features/review/assistant/useAskAssistant'
import { useQueueCases } from '@/features/review/assistant/useQueueCases'
import { useSourceDrawer } from '@/features/review/assistant/useSourceDrawer'
import { SourceDrawer } from '@/features/review/case-detail/components/SourceDrawer'
import { useDocumentTitle } from '@/modules/document-title/useDocumentTitle'

/** Breathing room kept above a newly asked question when it is scrolled to the top. */
const THREAD_TOP_GAP_PX = 16

/**
 * Asisten Bukti (`/assistant`) — the bounded, evidence-cited assistant (ADR-0007).
 *
 * The scope lives in the URL (`?case=<id>`), so a case card's "look into it here" and a link from
 * anywhere else land on the same state, and the browser's back button undoes a scope change. The
 * conversation lives in the tab's memory only.
 *
 * Layout is the one page in the app with `height="fill"`: the thread scrolls inside its own
 * bounded region while the input stays on the frame's bottom edge.
 */
export function AssistantPage() {
  const { t } = useTranslation('assistant')
  useDocumentTitle(t('page.title'))

  const [params, setParams] = useSearchParams()
  const caseParam = params.get('case')
  const scope: AssistantScope = caseParam ? { kind: 'CASE', case_id: caseParam } : QUEUE_SCOPE

  const { turns, isBusy, ask, stop, reset } = useAskAssistant()
  const queue = useQueueCases()
  const drawer = useSourceDrawer()
  const suggestions = useSuggestions()
  const input = useRef<HTMLTextAreaElement>(null)

  const scopeCase =
    scope.kind === 'CASE' ? (queue.cases.find((entry) => entry.row.case_id === scope.case_id) ?? null) : null
  const modes = scopeCase?.row.modes ?? []
  const lastAnswer = [...turns].reverse().find((turn) => turn.answer)?.answer ?? null

  // Focus goes back to the input after a scope change. From the scope menu it is handed over in
  // the menu's own close step — focusing here would lose to Radix returning focus to its trigger.
  const focusInput = useCallback(() => input.current?.focus(), [])
  const setScope = useCallback(
    (next: AssistantScope) => setParams(next.kind === 'CASE' ? { case: next.case_id } : {}),
    [setParams],
  )

  const askInScope = useCallback(
    (question: string) => {
      ask(question, scope)
      focusInput()
    },
    [ask, scope, focusInput],
  )

  const actions: AnswerActions = useMemo(
    () => ({
      onOpenResource: drawer.open,
      onFocusCase: (caseId: string) => {
        setScope({ kind: 'CASE', case_id: caseId })
        focusInput()
      },
      onAsk: askInScope,
      onRetry: (turn: Turn) => ask(turn.question, turn.scope),
    }),
    [drawer.open, setScope, focusInput, askInScope, ask],
  )

  // A new question is brought to the top of the thread, and its answer fills in below it — the
  // reviewer reads the answer from its first sentence instead of being dropped at its last. When
  // the answer lands it is aligned once more, because while it was being prepared there may not
  // have been enough below the question for it to reach the top — **unless the reviewer has
  // scrolled since**: someone re-reading an earlier turn is never pulled away from it.
  const thread = useRef<HTMLElement | null>(null)
  const isOurScroll = useRef(false)
  const hasReaderScrolled = useRef(false)
  const attachThread = useCallback((element: HTMLElement | null) => {
    thread.current = element
    element?.addEventListener('scroll', () => {
      if (isOurScroll.current) {
        isOurScroll.current = false
        return
      }
      hasReaderScrolled.current = true
    })
  }, [])

  const turnCount = turns.length
  const newestStatus = turns[turns.length - 1]?.status
  useEffect(() => {
    hasReaderScrolled.current = false
  }, [turnCount])
  useEffect(() => {
    const container = thread.current
    const newest = container?.querySelector<HTMLElement>('[data-turn]:last-of-type')
    if (!container || !newest || hasReaderScrolled.current) {
      return
    }
    const offset =
      newest.getBoundingClientRect().top - container.getBoundingClientRect().top + container.scrollTop
    const target = Math.max(0, offset - THREAD_TOP_GAP_PX)
    if (Math.abs(container.scrollTop - target) > 1) {
      isOurScroll.current = true
      container.scrollTop = target
    }
  }, [turnCount, newestStatus])

  // One quiet announcement per turn for screen readers, instead of a live region around the whole
  // thread re-reading every reading step and button as it renders.
  const announcement =
    newestStatus === 'streaming'
      ? t('turn.reading')
      : newestStatus === 'done'
        ? t('turn.ready')
        : newestStatus === 'stopped'
          ? t('turn.stopped')
          : newestStatus === 'failed'
            ? t('failure.heading')
            : ''

  return (
    <PageShell width="wide" height="fill">
      <PageHeader
        eyebrow={t('page.eyebrow')}
        title={t('page.title')}
        lede={t('page.lede')}
        className="mb-[16px]"
        action={
          turns.length > 0 ? (
            <Button variant="outline" onClick={reset}>
              <SquarePen aria-hidden />
              {t('page.newConversation')}
            </Button>
          ) : null
        }
      />

      <div className="flex min-h-0 flex-1 gap-[18px]">
        <div className="flex min-w-0 flex-1 flex-col overflow-hidden rounded-lg border border-line bg-card shadow-panel">
          <PerfectScrollArea className="flex-1" containerRef={attachThread}>
            <div
              role="log"
              aria-live="off"
              aria-busy={isBusy}
              aria-label={t('turn.conversation')}
              className="mx-auto flex min-h-full w-full max-w-[860px] flex-col gap-[30px] px-[24px] py-[24px]"
            >
              {turns.length === 0 ? (
                <EmptyState
                  scope={scope}
                  suggestions={suggestions(scope.kind, { modes })}
                  isDisabled={isBusy}
                  onPick={askInScope}
                />
              ) : (
                turns.map((turn, index) => (
                  <TurnView
                    key={turn.id}
                    turn={turn}
                    isLatest={index === turns.length - 1}
                    isBusy={isBusy}
                    modes={modes}
                    actions={actions}
                  />
                ))
              )}
            </div>
          </PerfectScrollArea>

          <div className="border-t border-line bg-sunk px-[18px] pt-[14px] pb-[12px]">
            <div className="mx-auto w-full max-w-[860px]">
              <p role="status" className="sr-only">
                {announcement}
              </p>
              {drawer.state.isOpening || drawer.state.hasFailed ? (
                <p role="status" className="mb-[8px] text-meta text-ink-3">
                  {drawer.state.isOpening ? t('answer.openingSource') : t('answer.sourceFailed')}
                </p>
              ) : null}
              <Composer
                ref={input}
                scope={scope}
                queue={queue}
                isBusy={isBusy}
                onScopeChange={setScope}
                onScopeChosen={focusInput}
                onAsk={askInScope}
                onStop={stop}
              />
            </div>
          </div>
        </div>

        <ContextPanel scope={scope} scopeCase={scopeCase} lastAnswer={lastAnswer} />
      </div>

      {drawer.state.detail ? (
        <SourceDrawer
          reference={drawer.state.reference}
          sources={drawer.state.detail.sources}
          versions={drawer.state.detail.versions}
          onClose={drawer.close}
        />
      ) : null}
    </PageShell>
  )
}

import { useTranslation } from 'react-i18next'

import type { TurnFailure } from '@/features/review/assistant/conversation'
import type { AnswerIntent, ScopeKind } from '@/features/review/assistant/types'
import type { BriefingPhase, GeneratedBy } from '@/features/review/case-briefing/types'
import type { RiskMode } from '@/features/review/shared/types'
import { translateOr } from '@/modules/i18n/translateOr'

/**
 * Copy for the assistant page, as hooks so a language switch re-renders it (see
 * `features/review/shared/labels.ts` for why constants cannot do that).
 *
 * The page is named "Asisten Bukti" by ADR-0007, and "AI" appears nowhere in either language.
 * How an answer was made is stated after the answer, never as a badge over it.
 */

const PHASES: readonly BriefingPhase[] = ['STARTED', 'READING', 'VALIDATING', 'DONE']

/** A phase the server grows later reads as "preparing", never as its raw key. */
export function usePhaseLabel(): (phase: BriefingPhase) => string {
  const { t } = useTranslation('assistant')
  return (phase) => (PHASES.includes(phase) ? t(`phase.${phase}` as 'phase.DONE') : t('turn.reading'))
}

export function useGeneratedByLabel(): (generatedBy: GeneratedBy) => string {
  const { t } = useTranslation('assistant')
  return (generatedBy) => t(`generatedBy.${generatedBy}` as 'generatedBy.TEMPLATE')
}

/**
 * What a reading step read, in words. The queue tools are this page's own; the seven case tools
 * are the briefing's and keep the briefing's names, so one step reads the same on both surfaces.
 */
export function toolLabel(tool: string): string {
  // The last fallback is a word, not the function name: a read the app has no name for yet is
  // still a read, and `get_something_new` is a machine token on the reading surface.
  return translateOr(
    `assistant:tool.${tool}`,
    translateOr(`briefing:tool.${tool}`, translateOr('assistant:tool.generic', 'Membaca data')),
  )
}

const KNOWN_FAILURES = ['CASE_NOT_FOUND', 'CASE_ACCESS_FORBIDDEN', 'ASSISTANT_UNAVAILABLE'] as const

/**
 * A failure in plain words. The code and the server's sentence stay one click away, in the
 * technical-details disclosure — never on the reading surface.
 */
export function useFailureMessage(): (failure: TurnFailure) => string {
  const { t } = useTranslation('assistant')
  return (failure) => {
    if (failure.code && (KNOWN_FAILURES as readonly string[]).includes(failure.code)) {
      return t(`failure.${failure.code}` as 'failure.CASE_NOT_FOUND')
    }
    return failure.code ? t('failure.generic') : t('failure.network')
  }
}

export type Suggestion = { readonly key: string; readonly question: string }

const QUEUE_KEYS = ['QUEUE_OVERVIEW', 'WHERE_TO_START', 'CASES_MATCHING', 'CONFLICTS'] as const
const CASE_KEYS = [
  'WHY_RAISED',
  'MISSING_EVIDENCE',
  'COUNTER_EVIDENCE',
  'TIMELINE',
  'COMPARISON',
] as const

/** Only these two modes produce a comparison pair; offering the question elsewhere is a dead end. */
const COMPARISON_MODES: readonly RiskMode[] = ['REPEAT_BILLING', 'CLONED_DOCUMENTATION']

/**
 * The questions offered as chips — on the empty page, after a refusal, and as follow-ups.
 *
 * Every one of them is a question the deterministic template recognises; a backend test reads
 * this locale file to make sure, so a chip can never answer "not recognised" in an offline demo.
 */
export function useSuggestions(): (
  scope: ScopeKind,
  options?: { readonly exclude?: AnswerIntent | null; readonly modes?: readonly RiskMode[] },
) => readonly Suggestion[] {
  const { t } = useTranslation('assistant')
  return (scope, options = {}) => {
    if (scope === 'QUEUE') {
      return QUEUE_KEYS.filter((key) => key !== options.exclude).map((key) => ({
        key,
        question: t(`suggestions.queue.${key}` as 'suggestions.queue.QUEUE_OVERVIEW'),
      }))
    }
    const comparable = (options.modes ?? []).some((mode) => COMPARISON_MODES.includes(mode))
    return CASE_KEYS.filter((key) => key !== options.exclude)
      .filter((key) => key !== 'COMPARISON' || comparable)
      .map((key) => ({
        key,
        question: t(`suggestions.case.${key}` as 'suggestions.case.WHY_RAISED'),
      }))
  }
}

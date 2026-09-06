import { useTranslation } from 'react-i18next'

import type {
  DispositionAction,
  Reason,
  ResourceType,
  SourceAvailability,
  SupportState,
} from '@/features/review/case-detail/types'
import { translateOr } from '@/modules/i18n/translateOr'

/**
 * Vocabulary for the case-detail screen, and the standard reasons a reviewer picks from.
 *
 * The **reason sentences** are never composed here — they arrive from the backend's catalog, so
 * the queue and this screen cannot disagree about why a case was raised, and so English and
 * Indonesian render one finding rather than two. What lives here is the vocabulary the screen
 * adds on top: action names, disposition reasons, resource names.
 *
 * Everything is a hook because a constant record is read once at module load and would keep its
 * language after the header switch. The two exceptions are `reasonStrength`, which is arithmetic
 * rather than words, and the `translateOr` lookups, which take a runtime key from the API.
 */

export function useActionLabel(): (action: DispositionAction) => string {
  const { t } = useTranslation('caseDetail')
  return (action) => t(`action.${action}` as 'action.ESCALATE')
}

/** What each action actually does, so a reviewer is never guessing at consequences. */
export function useActionMeaning(): (action: DispositionAction) => string {
  const { t } = useTranslation('caseDetail')
  return (action) => t(`actionMeaning.${action}` as 'actionMeaning.ESCALATE')
}

/**
 * The standard reasons offered per action.
 *
 * The system suggests; it never chooses. `brief/04_DETAIL_KASUS_DISPOSISI.md` § 7 is explicit
 * that nothing here may pre-select a reason or fill one in and save.
 */
export function useStructuredReasons(): (action: DispositionAction) => readonly string[] {
  const { t } = useTranslation('caseDetail')
  return (action) =>
    t(`structuredReason.${action}` as 'structuredReason.ESCALATE', {
      returnObjects: true,
    }) as unknown as readonly string[]
}

export function useSupportLabel(): (state: SupportState) => string {
  const { t } = useTranslation('caseDetail')
  // `NOT_ASSESSABLE` is not a softer "unsupported". The file was too thin to judge — that is a
  // different finding, and both languages keep it a different word.
  return (state) => t(`support.${state}` as 'support.SUPPORTED')
}

export function useSupportMeaning(): (state: SupportState) => string {
  const { t } = useTranslation('caseDetail')
  return (state) => t(`supportMeaning.${state}` as 'supportMeaning.SUPPORTED')
}

export function useResourceLabel(): (resourceType: ResourceType) => string {
  const { t } = useTranslation('caseDetail')
  return (resourceType) => t(`resource.${resourceType}` as 'resource.Claim')
}

export function useAvailabilityLabel(): (availability: SourceAvailability) => string {
  const { t } = useTranslation('caseDetail')
  return (availability) => t(`availability.${availability}` as 'availability.PRESENT')
}

export function useAvailabilityMeaning(): (availability: SourceAvailability) => string {
  const { t } = useTranslation('caseDetail')
  return (availability) => t(`availabilityMeaning.${availability}` as 'availabilityMeaning.PRESENT')
}

/** Field names inside a raw resource, so the source panel is readable without a schema. */
export function sourceFieldLabel(name: string): string {
  return translateOr(`caseDetail:sourceField.${name}`, name)
}

/** Component-score keys, which are rule internals and unreadable without a translation. */
export function componentLabel(name: string): string {
  return translateOr(`caseDetail:component.${name}`, name)
}

/**
 * Every `event_kind` the API can write. Kept exhaustive on purpose — an unlabelled kind falls
 * through to the raw enum, and `OPENED` shipped that way for a while: the audit tab read
 * "OPENED" in the middle of an otherwise Indonesian history.
 */
export function auditKindLabel(kind: string): string {
  return translateOr(`caseDetail:auditKind.${kind}`, kind)
}

export function actorLabel(role: string): string {
  return translateOr(`caseDetail:actor.${role}`, role)
}

export type Strength = 1 | 2 | 3

/**
 * How strongly the evidence supports one reason, on the three-step scale the card draws.
 *
 * Deterministic means a rule was violated for certain; a scored reason is a resemblance worth
 * looking at. Counter-evidence lowers either one, because an argument against a signal is part
 * of how strong that signal actually is — not a footnote under it.
 *
 * This mirrors the ordering the API applies (`order_by_strength`), so the meter never
 * contradicts the sequence the cards arrive in. It is arithmetic, not words, so it stays a plain
 * function — the *name* for its result is what needs a language.
 */
export function reasonStrength(reason: Reason): Strength {
  const weakened = reason.counter_evidence_notes.length > 0
  if (reason.deterministic) {
    return weakened ? 2 : 3
  }
  return weakened ? 1 : 2
}

export function useStrengthLabel(): (reason: Reason) => string {
  const { t } = useTranslation('caseDetail')
  return (reason) => t(`strength.${reasonStrength(reason)}` as 'strength.1')
}

/**
 * The Evidence Matrix's four cell states (ADR-0004). Each has words as well as a colour, and
 * the words differ in kind: two describe the record, one describes a defect in the reference,
 * and one says nothing was asked — which is not the same as nothing was found.
 */
export type MatrixCellState = 'FOUND' | 'MISSING' | 'UNRESOLVED' | 'NOT_EXPECTED'

export function useMatrixCellLabel(): (state: MatrixCellState) => string {
  const { t } = useTranslation('caseDetail')
  return (state) => t(`matrixCell.${state}` as 'matrixCell.FOUND')
}

export function useMatrixCellMeaning(): (state: MatrixCellState) => string {
  const { t } = useTranslation('caseDetail')
  return (state) => t(`matrixCellMeaning.${state}` as 'matrixCellMeaning.FOUND')
}

/** Lane names for the episode swimlane. Unknown kinds fall through to the raw kind. */
export function laneLabel(kind: string): string {
  return translateOr(`caseDetail:lane.${kind}`, kind)
}

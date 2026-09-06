import { useTranslation } from 'react-i18next'

import type { CaseState, PriorityBand, RiskMode } from '@/features/review/shared/types'

/**
 * Labels for the wire enums, in the reader's language.
 *
 * Reason *sentences* are never composed here — they come from the backend's reason catalog so
 * the queue and the case detail cannot disagree about why a case was raised, and so both
 * languages render one finding rather than two. These hooks cover only the enum values, which
 * have no sentence of their own.
 *
 * Each is a hook rather than a constant record because a record is read once at module load: it
 * would keep whichever language was active when the bundle first evaluated, and go on rendering
 * it after the header switch.
 */

export function useModeLabel(): (mode: RiskMode) => string {
  const { t } = useTranslation('review')
  return (mode) => t(`mode.${mode}` as 'mode.REPEAT_BILLING')
}

export function useBandLabel(): (band: PriorityBand) => string {
  const { t } = useTranslation('review')
  // Never "bersih" and never "clean". The system observed nothing; that is not a clearance.
  return (band) => t(`band.${band}` as 'band.NEEDS_CONTEXT')
}

/** Answers the queue's "why this band?" hover. */
export function useBandBasis(): (band: PriorityBand) => string {
  const { t } = useTranslation('review')
  return (band) => t(`bandBasis.${band}` as 'bandBasis.NEEDS_CONTEXT')
}

export function useStateLabel(): (state: CaseState) => string {
  const { t } = useTranslation('review')
  return (state) => t(`state.${state}` as 'state.SCREENED')
}

import { useTranslation } from 'react-i18next'

import type {
  BriefingPhase,
  GeneratedBy,
  ObservationKind,
} from '@/features/review/case-briefing/types'
import { translateOr } from '@/modules/i18n/translateOr'

/**
 * Copy for the briefing panel.
 *
 * The panel is named for what it is — a summary of evidence — and never for how it is made.
 * `01_product_decision.md` makes "readers describe it as an AI fraud detector / chatbot" a kill
 * criterion, so nothing here says agent, AI, or assistant in either language, and the
 * provenance line states the mechanism only after the content.
 */

export function useKindLabel(): (kind: ObservationKind) => string {
  const { t } = useTranslation('briefing')
  return (kind) => t(`kind.${kind}` as 'kind.EVIDENCE_GAP')
}

export function useConfidenceLabel(): (confidence: 'STATED' | 'INFERRED') => string {
  const { t } = useTranslation('briefing')
  return (confidence) => t(`confidence.${confidence}` as 'confidence.STATED')
}

export function usePhaseLabel(): (phase: BriefingPhase) => string {
  const { t } = useTranslation('briefing')
  return (phase) => t(`phase.${phase}` as 'phase.DONE')
}

export function useGeneratedByLabel(): (generatedBy: GeneratedBy) => string {
  const { t } = useTranslation('briefing')
  return (generatedBy) => t(`generatedBy.${generatedBy}` as 'generatedBy.TEMPLATE')
}

/** The seven read-only tools, so the progress log reads as what was read, not as function names. */
export function toolLabel(tool: string): string {
  return translateOr(`briefing:tool.${tool}`, tool)
}

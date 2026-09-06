import { useTranslation } from 'react-i18next'

import type { ValidationStatus } from '@/features/review/ingest/types'
import { translateOr } from '@/modules/i18n/translateOr'

/**
 * Vocabulary for the ingest screen.
 *
 * The **completeness notes** are never composed here — they arrive from the backend already
 * rendered in the language the request asked for, so the ingest report and the case detail
 * cannot disagree about what a submission was missing.
 */

export function useStatusLabel(): (status: ValidationStatus) => string {
  const { t } = useTranslation('ingest')
  return (status) => t(`status.${status}` as 'status.VALID')
}

/**
 * What each status means for what happens next.
 *
 * `VALID_WITH_NOTES` gets the longest explanation on purpose: it is the one a reader is most
 * likely to round to "invalid", and rounding it that way is the mistake the whole distinction
 * exists to prevent.
 */
export function useStatusMeaning(): (status: ValidationStatus) => string {
  const { t } = useTranslation('ingest')
  return (status) => t(`statusMeaning.${status}` as 'statusMeaning.VALID')
}

/**
 * Stable error codes translated into what went wrong and what to do about it.
 *
 * The API's own `detail` names the offending resource precisely and is kept beside this — but
 * it is written for an engineer reading a log. `docs/canonical/` requires the ingest report to
 * be *actionable*: the operator has to learn which resource to fix, not merely that something
 * somewhere is wrong.
 *
 * A code we have not explained falls back to a general sentence rather than to the raw code:
 * unlike a capability name, `BUNDLE_SCHEMA_INVALID` tells an operator nothing they can act on,
 * and the server's `detail` is rendered beside it either way.
 */
export function useIssueExplanation(): (code: string) => string {
  const { t } = useTranslation('ingest')
  return (code) => translateOr(`ingest:issue.${code}`, t('issue.fallback'))
}

/** Resource-type names for the count summary. */
export function countLabel(resourceType: string): string {
  return translateOr(`ingest:count.${resourceType}`, resourceType)
}

/**
 * The order the count cards are shown in.
 *
 * The API returns them alphabetically, which puts `Account` and `ChargeItem` — billing plumbing
 * — ahead of the claim and its lines. A reader checking that a submission arrived intact looks
 * for the claim first and the invoice last. The order lives here and not in the locale files:
 * a translator reordering a JSON object would reorder the cards.
 */
export const COUNT_ORDER: readonly string[] = [
  'Claim',
  'ClaimLine',
  'Encounter',
  'Condition',
  'Procedure',
  'Medication',
  'Diagnostic',
  'Document',
  'ChargeItem',
  'Invoice',
  'Account',
]

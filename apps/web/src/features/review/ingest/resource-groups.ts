import type { ResourceCount } from '@/features/review/ingest/types'

/**
 * The resource counts, arranged into the three questions a reviewer actually asks of a
 * submission: what is being claimed, what supports it, and how it was priced.
 *
 * The API returns the counts alphabetically, which puts `Account` and `ChargeItem` — billing
 * plumbing — ahead of the claim and its lines. Eleven equally weighted numbers in that order
 * ask the reader to do the arranging themselves, every time.
 *
 * **`present` counts kinds, not records.** Two charge items are one kind that arrived. The
 * question this summary answers is which categories reached the system at all, because that is
 * the one an operator can act on: a missing category is a document request, and a missing
 * record inside a present category is not visible from a count either way.
 *
 * Nothing here judges the submission. A category that did not arrive lowers certainty
 * downstream and is never a signal — see `apps/backend/app/service/validation.py`
 * § completeness notes, which draws the same line on the other side of the wire.
 */

export type ResourceGroupKey = 'billing' | 'clinical' | 'charges' | 'other'

/**
 * Which types belong to which group, and the order they are read in within it.
 *
 * The order lives here rather than in the locale files: a translator reordering a JSON object
 * would silently reorder the rows.
 */
const GROUP_MEMBERS: readonly (readonly [ResourceGroupKey, readonly string[]])[] = [
  ['billing', ['Claim', 'ClaimLine']],
  ['clinical', ['Encounter', 'Condition', 'Procedure', 'Medication', 'Diagnostic', 'Document']],
  ['charges', ['ChargeItem', 'Invoice', 'Account']],
]

const GROUPED_TYPES: ReadonlySet<string> = new Set(
  GROUP_MEMBERS.flatMap(([, types]) => types),
)

export type ResourceGroup = {
  readonly key: ResourceGroupKey
  readonly counts: readonly ResourceCount[]
  /** Types in this group that arrived with at least one record. */
  readonly present: number
  readonly total: number
}

export type ResourceCoverage = {
  readonly groups: readonly ResourceGroup[]
  readonly present: number
  readonly total: number
}

export function groupResourceCounts(counts: readonly ResourceCount[]): ResourceCoverage {
  const groups = [
    ...GROUP_MEMBERS.map(([key, types]) =>
      toGroup(
        key,
        types.flatMap((type) => counts.filter((count) => count.resource_type === type)),
      ),
    ),
    // A type this app has not been taught is still evidence that arrived. Dropping it would
    // understate the submission, so it keeps its place at the end in the order the API sent it.
    toGroup(
      'other',
      counts.filter((count) => !GROUPED_TYPES.has(count.resource_type)),
    ),
  ].filter((group) => group.total > 0)

  return {
    groups,
    present: groups.reduce((running, group) => running + group.present, 0),
    total: groups.reduce((running, group) => running + group.total, 0),
  }
}

function toGroup(key: ResourceGroupKey, counts: readonly ResourceCount[]): ResourceGroup {
  return {
    key,
    counts,
    present: counts.filter((count) => count.count > 0).length,
    total: counts.length,
  }
}

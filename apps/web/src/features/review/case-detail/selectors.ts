import type {
  CaseDetail,
  ComparisonCandidate,
  ResourceType,
} from '@/features/review/case-detail/types'

/**
 * Resource types the reasons expected but did not find.
 *
 * This is what "Minta bukti tambahan" ticks by default. It is computed from the same two
 * fields the reason card renders — `expected_support` against the types actually present in
 * `evidence` — so the checklist and the evidence panel can never tell different stories about
 * what is missing.
 */
export function missingEvidenceTypes(detail: CaseDetail): readonly ResourceType[] {
  const found = new Set(
    detail.reasons.flatMap((reason) => reason.evidence.map((ref) => ref.resource_type)),
  )
  const missing = detail.reasons.flatMap((reason) =>
    reason.expected_support.filter((type) => !found.has(type)),
  )
  return [...new Set(missing)]
}

/** Every resource type a reviewer may ask for, expected-but-missing ones first. */
export function requestableEvidenceTypes(detail: CaseDetail): readonly ResourceType[] {
  const expected = [...new Set(detail.reasons.flatMap((reason) => reason.expected_support))]
  const missing = missingEvidenceTypes(detail)
  const rest = expected.filter((type) => !missing.includes(type))
  const fallback: readonly ResourceType[] = ['Procedure', 'Document', 'Encounter', 'Medication']
  const offered = [...missing, ...rest]
  return offered.length > 0 ? offered : fallback
}

/**
 * The comparison belonging to the reason at `index`, if it has one.
 *
 * Matched by position among the comparison-shaped reasons rather than by an id, because the API
 * emits comparisons in reason order for exactly the two modes that have them. A reason whose
 * mode is not comparison-shaped has none, and offering a "Bandingkan" button that opens someone
 * else's pair would be worse than offering no button.
 */
export function comparisonForReason(
  detail: CaseDetail,
  index: number,
): ComparisonCandidate | null {
  const comparable = detail.reasons
    .map((entry, position) => ({ entry, position }))
    .filter(({ entry }) =>
      ['REPEAT_BILLING', 'CLONED_DOCUMENTATION'].includes(entry.mode),
    )
  const rank = comparable.findIndex(({ position }) => position === index)
  return rank >= 0 ? (detail.comparisons[rank] ?? null) : null
}

/** The line that caused the strongest reason, so the screen opens on what raised it. */
export function primaryLineId(detail: CaseDetail): string | null {
  const cited = detail.reasons[0]?.evidence.find((ref) => ref.resource_type === 'ClaimLine')
  if (cited && detail.lines.some((line) => line.line_id === cited.resource_id)) {
    return cited.resource_id
  }
  const unsupported = detail.lines.find((line) => line.support_state !== 'SUPPORTED')
  return unsupported?.line_id ?? detail.lines[0]?.line_id ?? null
}

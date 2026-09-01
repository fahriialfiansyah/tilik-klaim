/**
 * One rendering of a number, shared by every table and every chart on this page.
 *
 * `sprint/00-app-spec.md` § 6 makes "chart values = table values" a binding display rule, and
 * the usual way that breaks is two components formatting the same number differently. Both read
 * the same response and both call this, so a mismatch cannot be a rounding difference — it would
 * have to be a genuine integrity defect, which is exactly what the rule is there to catch.
 */

const DECIMALS = 4

export function formatMetric(value: number | null | undefined): string | null {
  return typeof value === 'number' && Number.isFinite(value) ? value.toFixed(DECIMALS) : null
}

/** A whole count. Support is a number of cases, not a measurement with decimals. */
export function formatCount(value: number | null | undefined): string | null {
  return typeof value === 'number' && Number.isFinite(value) ? String(Math.round(value)) : null
}

/** Milliseconds, in working language. */
export function formatLatency(milliseconds: number): string {
  return `${milliseconds} ms`
}

/** Bar width as a share of the largest measured value in the same chart. */
export function barShare(value: number, ceiling: number): number {
  if (!Number.isFinite(ceiling) || ceiling <= 0) {
    return 0
  }
  return Math.max(0, Math.min(1, value / ceiling))
}

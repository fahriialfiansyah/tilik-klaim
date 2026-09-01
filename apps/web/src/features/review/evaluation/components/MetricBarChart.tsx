import { NOT_MEASURED } from '@/features/review/evaluation/labels'
import { barShare, formatMetric } from '@/features/review/evaluation/format'

export type ChartRow = {
  readonly key: string
  readonly label: string
  readonly value: number | null
}

const PERCENT = 100

/**
 * Widgets 5 and 6 — bar charts drawn from the same rows the tables render.
 *
 * The value is printed beside every bar. That is not decoration: `sprint/00-app-spec.md` § 6
 * rule 2 makes chart-versus-table disagreement an integrity defect, and a printed number is what
 * lets a reader — and `EvaluationCharts.test.tsx` — check it against the table without measuring
 * pixels.
 *
 * A row with no measured value gets no bar at all. A zero-length bar reads as "measured, and it
 * was nothing", which is the misreading rule 4 exists to prevent.
 */
export function MetricBarChart({
  title,
  subtitle,
  rows,
}: {
  readonly title: string
  readonly subtitle: string
  readonly rows: readonly ChartRow[]
}) {
  const measured = rows.map((row) => row.value).filter((value): value is number => value !== null)
  const ceiling = measured.length > 0 ? Math.max(...measured) : 0

  return (
    <section className="rounded-md border border-line bg-card p-4">
      <h3 className="text-body-lg font-semibold text-ink">{title}</h3>
      <p className="mb-3 text-micro text-ink-2">{subtitle}</p>
      <ul className="space-y-2">
        {rows.map((row) => {
          const rendered = formatMetric(row.value)
          return (
            <li key={row.key} className="grid grid-cols-[minmax(0,9rem)_1fr_auto] items-center gap-3">
              <span className="truncate text-small text-ink">{row.label}</span>
              <span className="h-4 rounded-sm bg-sunk" aria-hidden="true">
                {row.value === null ? null : (
                  <span
                    className="block h-4 rounded-sm bg-brand"
                    style={{ width: `${barShare(row.value, ceiling) * PERCENT}%` }}
                  />
                )}
              </span>
              <span className="font-mono text-small tabular-nums text-ink">
                {rendered ?? <span className="font-sans italic text-ink-2">{NOT_MEASURED}</span>}
              </span>
            </li>
          )
        })}
      </ul>
    </section>
  )
}

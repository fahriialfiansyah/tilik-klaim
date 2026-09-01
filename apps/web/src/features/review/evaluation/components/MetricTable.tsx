import { NOT_MEASURED } from '@/features/review/evaluation/labels'
import { formatCount, formatMetric } from '@/features/review/evaluation/format'

export type MetricColumn = {
  readonly key: string
  readonly label: string
  /**
   * `count` renders a whole number. A case count shown as `24.0000` reads as a measurement
   * with four decimals of precision, which it is not — it is twenty-four cases.
   */
  readonly format?: 'metric' | 'count'
}

export type MetricRow = {
  readonly key: string
  readonly label: string
  readonly hint?: string
  /** A value of `null` was not measured, and is labelled as such rather than shown as zero. */
  readonly values: Readonly<Record<string, number | null>>
}

/**
 * One table shape for widgets 3 and 4.
 *
 * Every cell goes through `formatMetric`, the same function the charts use, so a bar and the
 * number beside it cannot disagree by a rounding step — which is what `sprint/00-app-spec.md`
 * § 6 rule 2 is there to prevent.
 */
export function MetricTable({
  caption,
  columns,
  rows,
}: {
  readonly caption: string
  readonly columns: readonly MetricColumn[]
  readonly rows: readonly MetricRow[]
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-small">
        <caption className="sr-only">{caption}</caption>
        <thead>
          <tr className="border-b border-line-strong text-left">
            <th scope="col" className="py-2 pr-3 font-semibold text-ink-2">
              Pendekatan
            </th>
            {columns.map((column) => (
              <th key={column.key} scope="col" className="py-2 pr-3 font-semibold text-ink-2">
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.key} className="border-b border-line align-top">
              <th scope="row" className="py-2 pr-3 text-left font-medium text-ink">
                {row.label}
                {row.hint ? (
                  <span className="block text-micro font-normal text-ink-2">{row.hint}</span>
                ) : null}
              </th>
              {columns.map((column) => {
                const value = row.values[column.key]
                const rendered =
                  column.format === 'count' ? formatCount(value) : formatMetric(value)
                return (
                  <td key={column.key} className="py-2 pr-3 font-mono tabular-nums text-ink">
                    {rendered ?? (
                      <span className="font-sans text-ink-2 italic">{NOT_MEASURED}</span>
                    )}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

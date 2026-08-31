import { issueExplanation } from '@/features/review/ingest/labels'
import type { ValidationIssue } from '@/features/review/ingest/types'
import { RESOURCE_LABELS } from '@/features/review/case-detail/labels'
import type { ResourceType } from '@/features/review/case-detail/types'

const HEAD_CLASS =
  'border-b border-line px-[15px] py-[9px] text-left font-mono text-micro font-semibold tracking-label text-ink-3'

function resourceLabel(resourceType: string | null): string {
  if (!resourceType) {
    return 'Seluruh berkas'
  }
  return RESOURCE_LABELS[resourceType as ResourceType] ?? resourceType
}

/**
 * Widget 6 — every problem found, pointed at the resource that caused it.
 *
 * Four columns, and the last two are the point. `docs/canonical/` requires this report to be
 * *actionable*: a stable code an operator can search for, the resource type and identifier they
 * have to open, and an explanation of what the code means. "Berkas tidak valid" is a message a
 * person can only resubmit against and hope.
 *
 * The explanation is this app's, in working language; the server's own `detail` sits beside it
 * because it names the offending value precisely and is what an engineer would want in a
 * ticket. Neither replaces the other.
 */
export function IssueTable({ issues }: { readonly issues: readonly ValidationIssue[] }) {
  return (
    <section
      aria-label="Galat dan peringatan"
      className="overflow-hidden rounded-lg border border-line bg-card shadow-panel"
    >
      <div className="border-b border-line px-4 py-[14px]">
        <p className="text-small font-semibold">
          Galat dan peringatan{' '}
          <span data-numeric className="font-normal text-ink-3">
            ({issues.length})
          </span>
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[720px] border-collapse">
          <thead>
            <tr className="bg-sunk">
              <th scope="col" style={{ width: '230px' }} className={HEAD_CLASS}>
                KODE
              </th>
              <th scope="col" style={{ width: '176px' }} className={HEAD_CLASS}>
                JENIS SUMBER DAYA
              </th>
              <th scope="col" style={{ width: '156px' }} className={HEAD_CLASS}>
                PENGENAL
              </th>
              <th scope="col" className={HEAD_CLASS}>
                PENJELASAN
              </th>
            </tr>
          </thead>
          <tbody>
            {issues.map((issue, index) => (
              <tr
                key={`${issue.code}-${issue.resource_id ?? index}`}
                className="border-b border-line align-top"
              >
                <td className="px-[15px] py-[11px]">
                  <span
                    data-numeric
                    className="inline-block rounded-sm border border-band-conflict-line bg-band-conflict-bg px-2 py-[2px] font-mono text-meta text-band-conflict"
                  >
                    {issue.code}
                  </span>
                </td>
                <td className="px-[15px] py-[11px] text-small">
                  {resourceLabel(issue.resource_type)}
                </td>
                <td
                  data-numeric
                  className="px-[15px] py-[11px] font-mono text-meta text-ink-2 break-all"
                >
                  {issue.resource_id ?? '—'}
                </td>
                <td className="px-[15px] py-[11px] text-small leading-relaxed text-pretty">
                  {issueExplanation(issue.code)}
                  <span className="mt-1 block font-mono text-micro text-ink-3 break-all">
                    {issue.detail}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

import { useTranslation } from 'react-i18next'

import { TechnicalDetails } from '@/features/review/ingest/components/TechnicalDetails'
import { useIssueExplanation } from '@/features/review/ingest/labels'
import type { ValidationIssue } from '@/features/review/ingest/types'
import { useResourceLabel } from '@/features/review/case-detail/labels'
import type { ResourceType } from '@/features/review/case-detail/types'

const HEAD_CLASS =
  'border-b border-line px-[15px] py-[9px] text-left font-mono text-micro font-semibold tracking-label text-ink-3'

/**
 * Widget 6 — every problem found, pointed at the resource that caused it.
 *
 * `docs/canonical/` requires this report to be *actionable*: the reader has to learn which
 * resource to open and what is wrong with it. So the three columns that survive are the ones a
 * reviewer can act on — the resource type, its identifier, and an explanation in their own
 * language.
 *
 * **The machine half is folded away rather than deleted.** A stable code and the service's own
 * sentence are exactly what a support request needs to quote, but they are written for an
 * engineer reading a log — the code names nothing a reviewer can do, and the service's `detail`
 * arrives in English whatever language the interface is in. Leading with either buries the
 * sentence that actually helps.
 */
export function IssueTable({ issues }: { readonly issues: readonly ValidationIssue[] }) {
  const { t } = useTranslation('ingest')
  const resourceTypeLabel = useResourceLabel()
  const issueExplanation = useIssueExplanation()

  /** The whole file, when the problem is not about one resource. */
  function resourceLabel(resourceType: string | null): string {
    return resourceType ? resourceTypeLabel(resourceType as ResourceType) : t('issues.wholeFile')
  }

  return (
    <section
      aria-label={t('issues.sectionLabel')}
      className="overflow-hidden rounded-lg border border-line bg-card shadow-panel"
    >
      <div className="border-b border-line px-4 py-[14px]">
        <p className="text-small font-semibold">
          {t('issues.heading')}{' '}
          <span data-numeric className="font-normal text-ink-3">
            ({issues.length})
          </span>
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[560px] border-collapse">
          <thead>
            <tr className="bg-sunk">
              <th scope="col" style={{ width: '188px' }} className={HEAD_CLASS}>
                {t('issues.resourceType')}
              </th>
              <th scope="col" style={{ width: '168px' }} className={HEAD_CLASS}>
                {t('issues.identifier')}
              </th>
              <th scope="col" className={HEAD_CLASS}>
                {t('issues.explanation')}
              </th>
            </tr>
          </thead>
          <tbody>
            {issues.map((issue, index) => (
              <tr
                key={`${issue.code}-${issue.resource_id ?? index}`}
                className="border-b border-line align-top"
              >
                <td className="px-[15px] py-[11px] text-small">
                  {resourceLabel(issue.resource_type)}
                </td>
                <td
                  data-numeric
                  className="px-[15px] py-[11px] font-mono text-meta text-ink-2 break-all"
                >
                  {issue.resource_id ?? t('issues.none')}
                </td>
                <td className="px-[15px] py-[11px] text-small leading-relaxed text-pretty">
                  {issueExplanation(issue.code)}
                  <TechnicalDetails code={issue.code} detail={issue.detail} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

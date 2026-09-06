import type { TFunction } from 'i18next'
import { useTranslation } from 'react-i18next'

import { countLabel } from '@/features/review/ingest/labels'
import {
  groupResourceCounts,
  type ResourceGroup,
} from '@/features/review/ingest/resource-groups'
import type { ResourceCount } from '@/features/review/ingest/types'
import { cn } from '@/lib/utils'

/**
 * Widget 5 — what the submission contained.
 *
 * Summary first, detail on request. The panel is scanned rather than read, and the question a
 * reviewer arrives with is "did this bundle turn up whole?" — eleven equally weighted numbers
 * make them answer it by counting. The tally answers it in one line; the per-type rows are a
 * fold away for the reader who needs to know *which* category is thin.
 *
 * **No colour carries a verdict here, by design.** `design/DESIGN.md` binds green to a
 * completed, validated action and red to a deterministic conflict, and neither describes a
 * submission that simply did not include medication data. Absence is drawn in the neutral band
 * and always named in words — a missing category is a document request, never an accusation.
 */
export function ResourceSummary({ counts }: { readonly counts: readonly ResourceCount[] }) {
  const { t } = useTranslation('ingest')
  const coverage = groupResourceCounts(counts)

  if (coverage.groups.length === 0) {
    return null
  }

  const everyCount = coverage.groups.flatMap((group) => group.counts)

  return (
    <div>
      <div className="px-4 py-[14px]">
        <div className="mb-[11px] flex items-baseline justify-between gap-3">
          <p className="font-mono text-micro font-semibold tracking-label text-ink-3">
            {t('report.coverageHeading')}
          </p>
          <p data-numeric className="font-mono text-body-lg font-semibold">
            {t('report.coverageTally', { present: coverage.present, total: coverage.total })}
          </p>
        </div>
        <Track counts={everyCount} />
      </div>

      {coverage.groups.map((group) => (
        <div
          key={group.key}
          className="flex items-center gap-3 border-t border-line px-4 py-[11px]"
        >
          <p className="w-[104px] shrink-0 text-small">{groupLabel(t, group.key)}</p>
          <div className="min-w-0 flex-1">
            <Track counts={group.counts} />
          </div>
          <p
            data-numeric
            className="w-[48px] shrink-0 text-right font-mono text-meta text-ink-2"
          >
            {t('report.groupTally', { present: group.present, total: group.total })}
          </p>
        </div>
      ))}

      <details className="border-t border-line">
        <summary className="cursor-pointer list-none bg-sunk px-4 py-[11px] text-small text-ink-2 marker:hidden hover:text-ink focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-brand">
          {t('report.detailToggle')}
        </summary>
        {coverage.groups.map((group) => (
          <GroupDetail key={group.key} group={group} />
        ))}
      </details>
    </div>
  )
}

/**
 * One segment per resource type, filled when that type arrived.
 *
 * Segments rather than a continuous bar: each one *is* a type, and the detail list below reads
 * in the same order, so the meter and the rows describe the same thing. A smooth bar would
 * imply a ratio scale this data does not have.
 *
 * Hidden from assistive technology on purpose — the tally beside it already says the number,
 * and reading eleven anonymous segments aloud would only add noise.
 */
function Track({ counts }: { readonly counts: readonly ResourceCount[] }) {
  return (
    <div aria-hidden className="flex gap-[2px]">
      {counts.map((count) => (
        <span
          key={count.resource_type}
          className={cn(
            'h-[9px] flex-1 rounded-[1px]',
            count.count > 0 ? 'bg-brand' : 'border border-band-quiet-line',
          )}
        />
      ))}
    </div>
  )
}

/** The folded rows: every type in the group, including the ones that did not arrive. */
function GroupDetail({ group }: { readonly group: ResourceGroup }) {
  const { t } = useTranslation('ingest')

  return (
    <div>
      <p className="border-t border-line bg-sunk px-4 py-2 font-mono text-micro font-semibold tracking-label text-ink-3">
        {groupLabel(t, group.key)}
      </p>
      {group.counts.map((count) => {
        const isAbsent = count.count === 0
        return (
          <div
            key={count.resource_type}
            className="flex items-center gap-[11px] border-t border-line px-4 py-[9px]"
          >
            <span
              aria-hidden
              className={cn(
                'size-[7px] shrink-0 rounded-full',
                isAbsent ? 'border-[1.5px] border-band-quiet-line' : 'bg-brand',
              )}
            />
            <span className={cn('min-w-0 flex-1 text-small', isAbsent && 'text-ink-3')}>
              {countLabel(count.resource_type)}
            </span>
            {isAbsent ? (
              <span className="rounded-sm border border-band-quiet-line bg-band-quiet-bg px-[7px] py-px text-meta text-ink-2">
                {t('report.absent')}
              </span>
            ) : null}
            <span
              data-numeric
              className={cn(
                'w-[18px] shrink-0 text-right font-mono text-small',
                isAbsent ? 'text-ink-3' : 'font-semibold',
              )}
            >
              {count.count}
            </span>
          </div>
        )
      })}
    </div>
  )
}

/** Group names live in the locale files; the reading order lives in `resource-groups.ts`. */
function groupLabel(t: TFunction<'ingest'>, key: ResourceGroup['key']): string {
  return t(`group.${key}` as 'group.billing')
}

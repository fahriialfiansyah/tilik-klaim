import { FileText, FolderOpen, ListOrdered } from 'lucide-react'
import type { ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'

import type { Citation } from '@/features/review/assistant/types'
import { cn } from '@/lib/utils'

/**
 * A citation opens what it names, and nothing else (ADR-0007 § 7).
 *
 * A resource opens in the same source drawer the case detail uses; a case opens its detail; the
 * queue opens the queue. Cases and the queue are real links, so they can be opened in a new tab
 * and are announced as links; a resource is a button, because it opens in place.
 */
function citationTarget(citation: Citation): string {
  if (citation.kind === 'CASE' && citation.case_id) {
    return `/cases/${encodeURIComponent(citation.case_id)}`
  }
  return '/'
}

function Actionable({
  citation,
  onOpenResource,
  className,
  label,
  children,
}: {
  readonly citation: Citation
  readonly onOpenResource: (citation: Citation) => void
  readonly className: string
  readonly label: string
  readonly children: ReactNode
}) {
  if (citation.kind === 'RESOURCE') {
    return (
      <button
        type="button"
        aria-label={label}
        title={citation.label}
        onClick={() => onOpenResource(citation)}
        className={className}
      >
        {children}
      </button>
    )
  }
  return (
    <Link to={citationTarget(citation)} aria-label={label} title={citation.label} className={className}>
      {children}
    </Link>
  )
}

/** The `[n]` beside a statement. Its number is the source's number in the list below. */
export function CitationChip({
  number,
  citation,
  onOpenResource,
}: {
  readonly number: number
  readonly citation: Citation
  readonly onOpenResource: (citation: Citation) => void
}) {
  const { t } = useTranslation('assistant')
  return (
    <Actionable
      citation={citation}
      onOpenResource={onOpenResource}
      label={t('answer.citation', { n: number, label: citation.label })}
      className="mx-[2px] inline-flex h-[18px] min-w-[20px] items-center justify-center rounded-sm border border-brand-line bg-brand-soft px-[5px] align-[1px] font-mono text-micro leading-none font-semibold text-brand transition-colors duration-[var(--motion-fast)] hover:bg-brand hover:text-brand-on"
    >
      <span data-numeric>{number}</span>
    </Actionable>
  )
}

const KIND_ICONS = { RESOURCE: FileText, CASE: FolderOpen, QUEUE: ListOrdered } as const

/** Every source an answer cites, numbered in the order the answer first cites it. */
export function SourceList({
  sources,
  onOpenResource,
}: {
  readonly sources: readonly Citation[]
  readonly onOpenResource: (citation: Citation) => void
}) {
  const { t } = useTranslation('assistant')
  return (
    <ol aria-label={t('answer.sourcesPlain')} className="grid gap-[6px] sm:grid-cols-2">
      {sources.map((source, index) => {
        const Icon = KIND_ICONS[source.kind]
        return (
          <li key={`${source.kind}:${source.case_id}:${source.resource_id}`}>
            <Actionable
              citation={source}
              onOpenResource={onOpenResource}
              label={t('answer.citation', { n: index + 1, label: source.label })}
              className={cn(
                'group flex w-full items-center gap-[9px] rounded-md border border-line bg-card px-[10px] py-[7px] text-left',
                'transition-colors duration-[var(--motion-fast)] hover:border-brand-line hover:bg-brand-soft',
              )}
            >
              <span
                data-numeric
                className="flex size-[20px] shrink-0 items-center justify-center rounded-sm bg-sunk font-mono text-micro font-semibold text-ink-2 group-hover:bg-card group-hover:text-brand"
              >
                {index + 1}
              </span>
              <Icon aria-hidden className="size-[14px] shrink-0 text-ink-3 group-hover:text-brand" />
              <span className="min-w-0 flex-1 truncate text-small text-ink group-hover:text-brand">
                {source.label}
              </span>
            </Actionable>
          </li>
        )
      })}
    </ol>
  )
}

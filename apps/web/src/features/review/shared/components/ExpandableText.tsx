import { useState } from 'react'

import { cn } from '@/lib/utils'

/** Long enough that it would push everything below it off the screen. */
const CLAMP_THRESHOLD = 240

/**
 * Long text, clamped with a control to see the rest.
 *
 * Two fields on the case-detail screen have no length the system controls: a clinical note in
 * the source panel, and the free-text note a reviewer writes on a disposition. Letting either
 * run at full length pushes the rest of a column out of view — the audit history stops being a
 * timeline and becomes one long paragraph with dates beside it.
 *
 * It **clamps rather than truncates**: the text is all there, and the control reveals it in
 * place. Cutting a clinical note off at an ellipsis on an evidence screen would be its own kind
 * of defect — the reviewer would have no way to know what the elision removed.
 */
export function ExpandableText({
  text,
  className,
  moreLabel = 'Tampilkan selengkapnya',
  lessLabel = 'Ringkaskan',
}: {
  readonly text: string
  readonly className?: string
  readonly moreLabel?: string
  readonly lessLabel?: string
}) {
  const [expanded, setExpanded] = useState(false)
  const isLong = text.length > CLAMP_THRESHOLD

  if (!isLong) {
    return <span className={cn('block break-words', className)}>{text}</span>
  }

  return (
    <span className="block">
      <span
        className={cn('block break-words', className, !expanded && 'line-clamp-4')}
        aria-expanded={expanded}
      >
        {text}
      </span>
      <button
        type="button"
        onClick={() => setExpanded((open) => !open)}
        className="mt-1 rounded-sm text-meta text-brand underline underline-offset-2 hover:text-brand-hover"
      >
        {expanded ? lessLabel : `${moreLabel} (${text.length} karakter)`}
      </button>
    </span>
  )
}

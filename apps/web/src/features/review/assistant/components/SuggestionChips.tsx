import { CornerDownLeft } from 'lucide-react'

import type { Suggestion } from '@/features/review/assistant/labels'

/**
 * Questions offered as one-click chips — after a refusal, after "not recognised", and as
 * follow-ups under the latest answer. A chip asks its question exactly as written, so what the
 * reviewer sees in the thread is what was sent.
 */
export function SuggestionChips({
  heading,
  suggestions,
  isDisabled,
  onPick,
}: {
  readonly heading: string
  readonly suggestions: readonly Suggestion[]
  readonly isDisabled: boolean
  readonly onPick: (question: string) => void
}) {
  if (suggestions.length === 0) {
    return null
  }
  return (
    <div>
      <p className="mb-[7px] font-mono text-micro font-semibold tracking-label text-ink-3">{heading}</p>
      <ul className="flex flex-wrap gap-[6px]">
        {suggestions.map((suggestion) => (
          <li key={suggestion.key}>
            <button
              type="button"
              disabled={isDisabled}
              onClick={() => onPick(suggestion.question)}
              className="group inline-flex items-center gap-[7px] rounded-full border border-line bg-card px-[12px] py-[5px] text-small text-ink-2 transition-colors duration-[var(--motion-fast)] hover:border-brand-line hover:bg-brand-soft hover:text-brand disabled:pointer-events-none disabled:opacity-50"
            >
              {suggestion.question}
              <CornerDownLeft aria-hidden className="size-3 text-ink-3 group-hover:text-brand" />
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}

import { SUPPORT_LABELS, SUPPORT_MEANINGS } from '@/features/review/case-detail/labels'
import type { ClaimLineView, SupportState } from '@/features/review/case-detail/types'
import { formatAmount, formatTime } from '@/features/review/shared/format'
import { cn } from '@/lib/utils'

/**
 * The four support states, each with its own colour **and** its own words.
 *
 * `NOT_ASSESSABLE` deliberately does not share a colour with `UNSUPPORTED`. "We could not judge
 * this" and "the evidence is absent" lead to different actions — asking for a document versus
 * questioning whether a service happened — and drawing them alike is how a thin record turns
 * into an allegation. Neither is red: red is reserved for a deterministic conflict, and an
 * unsupported line is an input to that finding, not the finding itself.
 */
const SUPPORT_CLASSES: Record<SupportState, string> = {
  SUPPORTED: 'border-line bg-sunk text-ink-2',
  PARTIALLY_SUPPORTED: 'border-band-context-line bg-band-context-bg text-band-context',
  UNSUPPORTED: 'border-band-signal-line bg-band-signal-bg text-band-signal',
  NOT_ASSESSABLE: 'border-band-quiet-line bg-band-quiet-bg text-band-quiet',
}

/** The rail marking which line is being read. */
const SUPPORT_RAIL: Record<SupportState, string> = {
  SUPPORTED: 'bg-line',
  PARTIALLY_SUPPORTED: 'bg-band-context',
  UNSUPPORTED: 'bg-band-signal',
  NOT_ASSESSABLE: 'bg-band-quiet',
}

/** The code arrives as a full terminology URI plus the code; only the code is readable. */
function shortCode(code: string): string {
  const parts = code.trim().split(/\s+/)
  return parts.at(-1) ?? code
}

/**
 * Widgets 8 and 9 — every billed line, with its support state.
 *
 * Selecting a line loads its evidence trail in the middle column, so each row is a real button
 * with `aria-pressed` rather than a click handler on a div. The line that caused the primary
 * reason is selected when the screen opens.
 */
export function ClaimLineList({
  lines,
  selectedLineId,
  onSelect,
}: {
  readonly lines: readonly ClaimLineView[]
  readonly selectedLineId: string | null
  readonly onSelect: (lineId: string) => void
}) {
  return (
    <section
      aria-label="Daftar baris tagihan"
      className="overflow-hidden rounded-lg border border-line bg-card shadow-panel"
    >
      <div className="border-b border-line px-[15px] py-[13px]">
        <p className="text-small font-semibold">Baris tagihan</p>
        <p className="mt-[2px] text-meta text-ink-3">Pilih baris untuk memuat jejak buktinya</p>
      </div>

      {lines.length === 0 ? (
        <p className="px-[15px] py-6 text-small text-ink-3">
          Bundel ini tidak memuat baris tagihan yang dapat ditampilkan.
        </p>
      ) : null}

      <ul>
        {lines.map((line) => {
          const isSelected = line.line_id === selectedLineId
          return (
            <li key={line.line_id}>
              <button
                type="button"
                aria-pressed={isSelected}
                onClick={() => onSelect(line.line_id)}
                className={cn(
                  'block w-full border-b border-line px-[15px] py-3 text-left hover:bg-sunk',
                  isSelected && 'bg-sunk',
                )}
              >
                <span
                  aria-hidden
                  className={cn(
                    'float-left -ms-[15px] me-[12px] h-[52px] w-[3px]',
                    isSelected ? SUPPORT_RAIL[line.support_state] : 'bg-transparent',
                  )}
                />
                <span className="mb-[3px] flex justify-between gap-2">
                  <span data-numeric className="font-mono text-meta text-ink-2">
                    {shortCode(line.code)}
                  </span>
                  <span data-numeric className="text-small font-medium">
                    {formatAmount(line.line_amount)}
                  </span>
                </span>
                <span className="mb-[6px] block text-small leading-snug">
                  {line.description}{' '}
                  <span className="text-ink-3">
                    · {line.quantity}× · {formatTime(line.service_at)}
                  </span>
                </span>
                <span
                  title={SUPPORT_MEANINGS[line.support_state]}
                  className={cn(
                    'inline-block rounded-sm border px-2 py-[2px] text-meta font-medium',
                    SUPPORT_CLASSES[line.support_state],
                  )}
                >
                  {SUPPORT_LABELS[line.support_state]}
                </span>
                <span className="sr-only"> — {SUPPORT_MEANINGS[line.support_state]}</span>
              </button>
            </li>
          )
        })}
      </ul>
    </section>
  )
}

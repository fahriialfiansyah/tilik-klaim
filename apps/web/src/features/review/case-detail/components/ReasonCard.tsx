import {
  RESOURCE_LABELS,
  reasonStrength,
  strengthLabel,
} from '@/features/review/case-detail/labels'
import type { EvidenceRef, Reason, SourceResource } from '@/features/review/case-detail/types'
import { EvidenceRefButton } from '@/features/review/case-detail/components/EvidenceRefButton'
import { MODE_LABELS } from '@/features/review/shared/labels'
import { cn } from '@/lib/utils'

const MICRO_LABEL = 'font-mono text-micro font-semibold tracking-label text-ink-3'
const STRENGTH_SEGMENTS = 3

/** Which expected resource types a reason actually found, so the gap between them is visible. */
function foundTypes(reason: Reason): ReadonlySet<string> {
  return new Set(reason.evidence.map((ref) => ref.resource_type))
}

/**
 * Widgets 10–13 — one reason, its expected and found evidence, and what argues against it.
 *
 * Two structural decisions here are binding rules rather than layout taste.
 *
 * **Counter-evidence is never inside the collapsible.** Display rule 2 gives it equal standing
 * with supporting evidence, and a panel a reviewer has to open first does not have equal
 * standing — it has whatever standing curiosity gives it. So the argument against the reason
 * renders in the card body, visible whether the card is expanded or not.
 *
 * **Every evidence reference opens.** Display rule 4 makes a reference to a resource that
 * cannot be shown a defect rather than a blank panel, so each one goes through
 * `EvidenceRefButton`, which resolves against the source index and says so when it cannot.
 */
export function ReasonCard({
  reason,
  isOpen,
  onToggle,
  sources,
  onOpenSource,
  onCompare,
}: {
  readonly reason: Reason
  readonly isOpen: boolean
  readonly onToggle: () => void
  readonly sources: readonly SourceResource[]
  readonly onOpenSource: (ref: EvidenceRef) => void
  readonly onCompare: (() => void) | null
}) {
  const strength = reasonStrength(reason)
  const found = foundTypes(reason)
  const bodyId = `alasan-${reason.code}`

  return (
    <article
      className={cn(
        'overflow-hidden rounded-lg border bg-card shadow-panel',
        reason.deterministic ? 'border-band-conflict-line' : 'border-line',
      )}
    >
      <h3>
        <button
          type="button"
          onClick={onToggle}
          aria-expanded={isOpen}
          aria-controls={bodyId}
          className={cn(
            'flex w-full items-start gap-[14px] border-s-[3px] px-4 py-[15px] text-left hover:bg-sunk',
            reason.deterministic ? 'border-s-band-conflict' : 'border-s-band-context',
          )}
        >
          <span className="min-w-0 flex-1">
            <span className="mb-[7px] flex flex-wrap items-center gap-[9px]">
              <span className="rounded-full border border-line bg-sunk px-[9px] py-[2px] text-meta">
                {MODE_LABELS[reason.mode]}
              </span>
              <span data-numeric className="font-mono text-micro text-ink-3">
                {reason.code} · aturan v{reason.ruleset_version}
              </span>
              <span className="flex items-center gap-[5px] text-meta text-ink-2">
                kekuatan
                <span aria-hidden className="flex gap-[2px]">
                  {Array.from({ length: STRENGTH_SEGMENTS }, (_, index) => (
                    <span
                      key={index}
                      className={cn(
                        'h-[4px] w-3 rounded-sm',
                        index < strength ? 'bg-ink-2' : 'bg-line-strong',
                      )}
                    />
                  ))}
                </span>
                {strengthLabel(reason)}
              </span>
            </span>
            <span className="block text-body-lg font-medium text-pretty">{reason.sentence}</span>
          </span>
          <span
            aria-hidden
            className="flex size-6 shrink-0 items-center justify-center rounded-md border border-line font-mono text-meta text-ink-2"
          >
            {isOpen ? '−' : '+'}
          </span>
        </button>
      </h3>

      {/*
        Widget 13 — outside the collapsible on purpose. See the note above the component.
        When a reason has none, the section says so rather than disappearing: an absent
        heading reads as "nothing was looked for", not as "nothing was found".
      */}
      <div className="px-4 pb-4">
        <div className="rounded-md border border-dashed border-line-strong bg-sunk px-[15px] py-[13px]">
          <p className={cn('mb-[5px] text-ink-2', MICRO_LABEL)}>
            BUKTI TANDINGAN — MELEMAHKAN ALASAN INI
          </p>
          {reason.counter_evidence_notes.length === 0 ? (
            <p className="text-small text-ink-2">
              Tidak ditemukan bukti tandingan untuk alasan ini pada bundel yang tersedia.
            </p>
          ) : (
            <ul className="space-y-[10px]">
              {reason.counter_evidence_notes.map((note) => (
                <li key={note.note}>
                  <p className="text-small leading-relaxed text-pretty">{note.note}</p>
                  {note.refs.length > 0 ? (
                    <p className="mt-1 flex flex-wrap gap-x-3 gap-y-1">
                      {note.refs.map((ref) => (
                        <EvidenceRefButton
                          key={`${ref.resource_type}:${ref.resource_id}`}
                          reference={ref}
                          sources={sources}
                          onOpen={onOpenSource}
                        />
                      ))}
                    </p>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {isOpen ? (
        <div id={bodyId} className="px-4 pb-4">
          <div className="mb-[14px] grid gap-[18px] sm:grid-cols-2">
            <div>
              <p className={cn('mb-[7px]', MICRO_LABEL)}>BUKTI YANG DIHARAPKAN</p>
              {reason.expected_support.length === 0 ? (
                <p className="text-small text-ink-3">
                  Aturan ini tidak menetapkan jenis bukti tertentu.
                </p>
              ) : (
                <ul>
                  {reason.expected_support.map((type) => (
                    <li
                      key={type}
                      className="flex items-center justify-between gap-2 border-t border-line py-[7px] text-small text-ink-2"
                    >
                      {RESOURCE_LABELS[type]}
                      <span
                        className={cn(
                          'text-meta',
                          found.has(type) ? 'text-ink-3' : 'text-band-signal',
                        )}
                      >
                        {found.has(type) ? 'ditemukan' : 'tidak ditemukan'}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div>
              <p className={cn('mb-[7px]', MICRO_LABEL)}>BUKTI YANG DITEMUKAN</p>
              {reason.evidence.length === 0 ? (
                <p className="text-small text-ink-3">
                  Tidak ada sumber daya pendukung yang ditemukan untuk alasan ini.
                </p>
              ) : (
                <ul>
                  {reason.evidence.map((ref) => (
                    <li
                      key={`${ref.resource_type}:${ref.resource_id}`}
                      className="border-t border-line py-[7px] text-small"
                    >
                      <EvidenceRefButton
                        reference={ref}
                        sources={sources}
                        onOpen={onOpenSource}
                      />
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          {onCompare ? (
            <button
              type="button"
              onClick={onCompare}
              className="rounded-md border border-line-strong bg-card px-[15px] py-2 text-small font-semibold hover:border-brand hover:text-brand"
            >
              Bandingkan pasangan kandidat
            </button>
          ) : null}
        </div>
      ) : null}
    </article>
  )
}

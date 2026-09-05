import { BriefingProgress } from '@/features/review/case-briefing/components/BriefingProgress'
import type { BriefingState } from '@/features/review/case-briefing/events'
import {
  CONFIDENCE_LABELS,
  GENERATED_BY_LABELS,
  KIND_LABELS,
  PANEL_SUBTITLE,
  PANEL_TITLE,
  RESTART_LABEL,
  START_LABEL,
} from '@/features/review/case-briefing/labels'
import { EvidenceRefButton } from '@/features/review/case-detail/components/EvidenceRefButton'
import type { EvidenceRef, SourceResource } from '@/features/review/case-detail/types'
import { cn } from '@/lib/utils'

const MICRO_LABEL = 'font-mono text-micro font-semibold tracking-label text-ink-3'

function Refs({
  refs,
  sources,
  onOpenSource,
}: {
  readonly refs: readonly EvidenceRef[]
  readonly sources: readonly SourceResource[]
  readonly onOpenSource: (reference: EvidenceRef) => void
}) {
  return (
    <p className="mt-1 flex flex-wrap gap-x-3 gap-y-1">
      {refs.map((ref) => (
        <EvidenceRefButton
          key={`${ref.resource_type}:${ref.resource_id}`}
          reference={ref}
          sources={sources}
          onOpen={onOpenSource}
        />
      ))}
    </p>
  )
}

/**
 * The briefing panel, presentational. Collapsed by default; **no action controls** — it cannot
 * pick a disposition, prefill a reason, or tick the evidence checklist, and it imports nothing
 * from the disposition store (a test reads this file to make sure).
 *
 * Reading order inside is binding too: observations, then questions, then the uncertainty
 * note, and only then how it was produced. Provenance is a footnote to the content, not a
 * headline over it.
 */
export function BriefingView({
  state,
  isOpen,
  onToggle,
  onStart,
  sources,
  onOpenSource,
}: {
  readonly state: BriefingState
  readonly isOpen: boolean
  readonly onToggle: () => void
  readonly onStart: () => void
  readonly sources: readonly SourceResource[]
  readonly onOpenSource: (reference: EvidenceRef) => void
}) {
  const briefing = state.briefing
  const bodyId = 'ringkasan-bukti'

  return (
    <section aria-label={PANEL_TITLE} className="rounded-lg border border-line bg-card shadow-panel">
      <h3>
        <button
          type="button"
          onClick={onToggle}
          aria-expanded={isOpen}
          aria-controls={bodyId}
          className="flex w-full items-start justify-between gap-3 px-[15px] py-[13px] text-left hover:bg-sunk"
        >
          <span>
            <span className="block text-small font-semibold">{PANEL_TITLE}</span>
            <span className="block text-meta text-ink-3 text-pretty">{PANEL_SUBTITLE}</span>
          </span>
          <span aria-hidden className="flex size-6 shrink-0 items-center justify-center rounded-md border border-line font-mono text-meta text-ink-2">
            {isOpen ? '−' : '+'}
          </span>
        </button>
      </h3>

      {isOpen ? (
        <div id={bodyId} className="border-t border-line px-[15px] py-[13px]">
          {state.status === 'idle' ? (
            <div className="flex flex-wrap items-center gap-3">
              <p className="text-small text-ink-2 text-pretty">
                Ringkasan disusun hanya dari bukti yang sudah ada di layar ini, dengan rujukan
                pada setiap pengamatan. Tidak ada yang diambil dari luar kasus ini.
              </p>
              <button
                type="button"
                onClick={onStart}
                className="rounded-md border border-line-strong bg-card px-[15px] py-2 text-small font-semibold hover:border-brand hover:text-brand"
              >
                {START_LABEL}
              </button>
            </div>
          ) : null}

          {state.status !== 'idle' ? <BriefingProgress state={state} /> : null}

          {state.status === 'failed' ? (
            <p role="alert" className="mt-3 text-small text-band-conflict">
              Ringkasan tidak dapat disusun: {state.error ?? 'layanan tidak merespons'}. Alasan
              dan bukti di atas tetap lengkap tanpa ringkasan ini.
            </p>
          ) : null}

          {state.observations.length > 0 ? (
            <>
              <p className={cn('mt-4 mb-2', MICRO_LABEL)}>PENGAMATAN</p>
              <ol className="space-y-3">
                {state.observations.map((observation) => (
                  <li key={observation.statement} className="rounded-md border border-line px-[13px] py-[10px]">
                    <p className="mb-1 flex flex-wrap items-center gap-2 text-meta text-ink-3">
                      <span className="rounded-full border border-line bg-sunk px-[9px] py-[1px]">
                        {KIND_LABELS[observation.kind]}
                      </span>
                      <span>{CONFIDENCE_LABELS[observation.confidence]}</span>
                    </p>
                    <p className="text-small leading-relaxed text-pretty">{observation.statement}</p>
                    <Refs refs={observation.source_refs} sources={sources} onOpenSource={onOpenSource} />
                  </li>
                ))}
              </ol>
            </>
          ) : null}

          {briefing && briefing.open_questions.length > 0 ? (
            <>
              <p className={cn('mt-4 mb-2', MICRO_LABEL)}>PERTANYAAN TERBUKA</p>
              <ul className="space-y-3">
                {briefing.open_questions.map((question) => (
                  <li key={question.question} className="rounded-md border border-dashed border-line-strong px-[13px] py-[10px]">
                    <p className="text-small font-medium text-pretty">{question.question}</p>
                    <p className="text-meta text-ink-2 text-pretty">{question.why_it_matters}</p>
                    <Refs refs={question.source_refs} sources={sources} onOpenSource={onOpenSource} />
                  </li>
                ))}
              </ul>
            </>
          ) : null}

          {briefing ? (
            <>
              <p className={cn('mt-4 mb-1', MICRO_LABEL)}>KETIDAKPASTIAN</p>
              <p className="text-small text-ink-2 text-pretty">{briefing.uncertainty_note}</p>

              <p className={cn('mt-4 mb-1', MICRO_LABEL)}>CARA DISUSUN</p>
              <p data-numeric className="text-meta text-ink-3">
                {GENERATED_BY_LABELS[briefing.generated_by]}
                {briefing.model_id ? ` · ${briefing.model_id}` : ''} · {briefing.prompt_version} ·
                aturan v{briefing.versions.ruleset_version}
                {state.viaFallback ? ' · dimuat tanpa aliran' : ''}
              </p>
              {briefing.validation_rejected ? (
                <p className="mt-1 text-meta text-notice text-pretty">
                  Keluaran model ditolak validator ({briefing.rejection_reason ?? 'tanpa alasan'}).
                  Yang tampil adalah templat deterministik.
                </p>
              ) : null}
              <button
                type="button"
                onClick={onStart}
                className="mt-3 rounded-md border border-line bg-card px-3 py-[6px] text-meta font-medium hover:border-brand hover:text-brand"
              >
                {RESTART_LABEL}
              </button>
            </>
          ) : null}
        </div>
      ) : null}
    </section>
  )
}

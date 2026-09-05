import { Check, Loader2 } from 'lucide-react'
import { useEffect, useMemo } from 'react'

import { Button } from '@/components/ui/button'
import {
  ACTION_LABELS,
  ACTION_MEANINGS,
  RESOURCE_LABELS,
  STRUCTURED_REASONS,
} from '@/features/review/case-detail/labels'
import { missingEvidenceTypes, requestableEvidenceTypes } from '@/features/review/case-detail/selectors'
import {
  EMPTY_DRAFT,
  isSavable,
  missingFieldLabel,
  useCaseDetailStore,
} from '@/features/review/case-detail/store'
import type { CaseDetail, DispositionAction } from '@/features/review/case-detail/types'
import { DISPOSITION_ACTIONS } from '@/features/review/case-detail/types'
import type { SaveStatus } from '@/features/review/case-detail/useCaseDetail'
import { cn } from '@/lib/utils'

const MICRO_LABEL = 'font-mono text-micro font-semibold tracking-label text-ink-3'

/**
 * Widgets 17–22 — where the decision is recorded.
 *
 * The save button stays disabled until an action **and** a reason are both present, and it says
 * which one is still missing rather than sitting there inert. That is a storage-level rule the
 * UI merely reflects: `apps/backend/app/service/disposition.py` refuses a blank reason, and a
 * check that lived only here could be bypassed by any client.
 *
 * Nothing in this panel pre-selects a reason. `brief/04_DETAIL_KASUS_DISPOSISI.md` § 7 allows
 * the system to *offer* standard reasons and forbids it from choosing one — the requested-
 * evidence checklist is the single thing that arrives pre-ticked, and every tick is editable.
 */
export function DispositionPanel({
  detail,
  saveStatus,
  onSave,
  panelRef,
}: {
  readonly detail: CaseDetail
  readonly saveStatus: SaveStatus
  readonly onSave: () => void
  readonly panelRef: React.RefObject<HTMLDivElement>
}) {
  const caseId = detail.case_id
  const draft = useCaseDetailStore((state) => state.drafts[caseId]) ?? EMPTY_DRAFT
  const setAction = useCaseDetailStore((state) => state.setAction)
  const setStructuredReason = useCaseDetailStore((state) => state.setStructuredReason)
  const setNote = useCaseDetailStore((state) => state.setNote)
  const seedRequestedEvidence = useCaseDetailStore((state) => state.seedRequestedEvidence)
  const toggleRequestedEvidence = useCaseDetailStore((state) => state.toggleRequestedEvidence)

  const needsEvidence = draft.action === 'REQUEST_EVIDENCE'
  // Memoised so the seeding effect below has a stable dependency. Both are pure functions of
  // the case, but each call returns a fresh array, which would re-run the effect every render.
  const missing = useMemo(() => missingEvidenceTypes(detail), [detail])
  const offered = useMemo(() => requestableEvidenceTypes(detail), [detail])

  useEffect(() => {
    if (needsEvidence) {
      seedRequestedEvidence(caseId, missing)
    }
  }, [caseId, needsEvidence, missing, seedRequestedEvidence])

  const savable = isSavable(draft)
  const blocking = missingFieldLabel(draft)
  const options = draft.action ? STRUCTURED_REASONS[draft.action] : []

  return (
    <div
      ref={panelRef}
      tabIndex={-1}
      aria-label="Panel disposisi"
      role="region"
      className="overflow-hidden rounded-lg border border-line bg-card shadow-panel lg:sticky lg:top-4"
    >
      <div className="border-b border-line bg-sunk px-4 py-[14px]">
        <p className="text-small font-semibold">Disposisi</p>
        <div className="mt-[7px] flex items-center gap-2">
          <span
            aria-hidden
            className={cn('h-[4px] flex-1 rounded-sm', draft.action ? 'bg-brand' : 'bg-line')}
          />
          <span
            aria-hidden
            className={cn('h-[4px] flex-1 rounded-sm', savable ? 'bg-brand' : 'bg-line')}
          />
          <span data-numeric className="font-mono text-micro text-ink-3">
            {savable ? '2/2' : draft.action ? '1/2' : '0/2'}
          </span>
        </div>
      </div>

      <div className="p-4">
        <fieldset className="mb-[18px]">
          <legend className={cn('mb-[9px]', MICRO_LABEL)}>TINDAKAN</legend>
          <div className="flex flex-col gap-[7px]">
            {DISPOSITION_ACTIONS.map((action: DispositionAction) => {
              const isPicked = draft.action === action
              return (
                <label
                  key={action}
                  className={cn(
                    // Selected and hovered must not look alike. Hover only firms the border;
                    // the filled ring plus the tinted ground belong to the chosen action alone,
                    // otherwise moving the pointer down the list makes each one look picked.
                    'flex cursor-pointer items-start gap-[10px] rounded-md border px-3 py-[10px] text-small font-semibold',
                    isPicked
                      ? 'border-brand bg-brand-soft'
                      : 'border-line bg-card hover:border-line-strong hover:bg-sunk',
                  )}
                >
                  {/*
                    Styled in place with `appearance-none` rather than hidden behind a drawn
                    stand-in. A visually hidden input still owns the accessible name, the
                    focus ring, and the radio group's arrow keys — but it is no longer where it
                    looks like it is, so a click lands on the label and hit-testing (a pointer
                    driver's, an assistive pointer's) misses the control entirely.

                    `bg-clip-content` with 3px of padding paints the background only inside the
                    content box, which is what draws the dot: a brand ring with a brand centre.
                  */}
                  <input
                    type="radio"
                    name="disposition-action"
                    value={action}
                    checked={isPicked}
                    onChange={() => setAction(caseId, action)}
                    className="mt-[2px] size-[15px] shrink-0 appearance-none rounded-full border-[1.5px] border-line-strong bg-card bg-clip-content p-[3px] checked:border-brand checked:bg-brand"
                  />
                  <span className="min-w-0">
                    {ACTION_LABELS[action]}
                    <span className="mt-[3px] block text-meta font-normal text-ink-2 text-pretty">
                      {ACTION_MEANINGS[action]}
                    </span>
                  </span>
                </label>
              )
            })}
          </div>
        </fieldset>

        <label htmlFor="alasan-terstruktur" className={cn('mb-[9px] block', MICRO_LABEL)}>
          ALASAN TERSTRUKTUR
        </label>
        <select
          id="alasan-terstruktur"
          value={draft.structuredReason}
          disabled={draft.action === null}
          onChange={(event) => setStructuredReason(caseId, event.target.value)}
          className="mb-[6px] w-full rounded-md border border-line bg-card px-[10px] py-[9px] text-small text-ink disabled:opacity-50"
        >
          <option value="">
            {draft.action ? 'Pilih alasan…' : 'Pilih tindakan terlebih dahulu'}
          </option>
          {options.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
        <p className="mb-4 text-meta text-ink-3 text-pretty">
          Alasan wajib dan tersimpan permanen. Sistem hanya menawarkan pilihan, tidak pernah
          memilihkan.
        </p>

        {needsEvidence ? (
          <fieldset className="mb-[18px] rounded-md border border-line bg-sunk px-[13px] py-3">
            <legend className={cn('px-1', MICRO_LABEL)}>BUKTI YANG DIMINTA</legend>
            {offered.map((type) => {
              const isTicked = draft.requestedEvidence.includes(type)
              return (
                <label
                  key={type}
                  className="flex cursor-pointer items-center gap-[9px] py-[5px] text-small"
                >
                  <span className="relative flex size-[15px] shrink-0 items-center justify-center">
                    <input
                      type="checkbox"
                      checked={isTicked}
                      onChange={() => toggleRequestedEvidence(caseId, type)}
                      className="peer size-[15px] appearance-none rounded-sm border-[1.5px] border-line-strong bg-card checked:border-brand checked:bg-brand"
                    />
                    {/* The tick sits over the input, so the control stays where it looks. */}
                    <span
                      aria-hidden
                      className="pointer-events-none absolute text-micro font-bold text-brand-on opacity-0 peer-checked:opacity-100"
                    >
                      ✓
                    </span>
                  </span>
                  {RESOURCE_LABELS[type]}
                </label>
              )
            })}
            <p className="mt-2 text-meta text-ink-3 text-pretty">
              Tercentang otomatis dari sumber daya yang kurang; boleh ditambah atau dikurangi.
            </p>
          </fieldset>
        ) : null}

        <label htmlFor="catatan-bebas" className={cn('mb-[9px] block', MICRO_LABEL)}>
          CATATAN BEBAS
        </label>
        <textarea
          id="catatan-bebas"
          rows={4}
          value={draft.note}
          onChange={(event) => setNote(caseId, event.target.value)}
          placeholder="Penjelasan tambahan untuk jejak audit"
          className="mb-[14px] w-full resize-y rounded-md border border-line bg-card p-[10px] text-small text-ink"
        />

        {/* Widget 21 — the version this decision is being made against. */}
        <p data-numeric className="mb-[14px] font-mono text-meta text-ink-3">
          versi kasus {detail.case_version} · aturan v{detail.versions.ruleset_version} · mesin v
          {detail.versions.engine_version}
        </p>

        <Button
          type="button"
          size="lg"
          className="w-full"
          disabled={!savable || saveStatus === 'saving'}
          onClick={onSave}
        >
          {saveStatus === 'saving' ? <Loader2 className="animate-spin" /> : null}
          {saveStatus === 'saved' ? <Check /> : null}
          Simpan disposisi
        </Button>
        <p
          aria-live="polite"
          className="mt-[9px] text-meta leading-relaxed text-ink-3 text-pretty"
        >
          {blocking ??
            'Keputusan ini tercatat permanen beserta pelaku, waktu, alasan, dan versi mesin.'}
        </p>
      </div>
    </div>
  )
}

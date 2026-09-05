import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { PageShell } from '@/components/layouts/PageShell'
import { BriefingPanel } from '@/features/review/case-briefing/components/BriefingPanel'
import { AuditTimeline } from '@/features/review/case-detail/components/AuditTimeline'
import {
  SaveFailedBanner,
  TemplateCaveatBanner,
  VersionConflictBanner,
} from '@/features/review/case-detail/components/CaseDetailBanners'
import {
  CaseDetailFailed,
  CaseDetailLoading,
} from '@/features/review/case-detail/components/CaseDetailPlaceholders'
import { CaseDrawerHost } from '@/features/review/case-detail/components/CaseDrawerHost'
import { CaseHeader } from '@/features/review/case-detail/components/CaseHeader'
import { ClaimLineList } from '@/features/review/case-detail/components/ClaimLineList'
import { ConfirmAnomalyDialog } from '@/features/review/case-detail/components/ConfirmAnomalyDialog'
import { DispositionPanel } from '@/features/review/case-detail/components/DispositionPanel'
import { EpisodeSwimlane } from '@/features/review/case-detail/components/EpisodeSwimlane'
import { EvidenceMap } from '@/features/review/case-detail/components/EvidenceMap'
import { EvidenceMatrix } from '@/features/review/case-detail/components/EvidenceMatrix'
import { ReasonCard } from '@/features/review/case-detail/components/ReasonCard'
import { buildEvidenceMatrix } from '@/features/review/case-detail/matrix'
import { comparisonForReason, primaryLineId } from '@/features/review/case-detail/selectors'
import { EMPTY_DRAFT, useCaseDetailStore } from '@/features/review/case-detail/store'
import type { DispositionAction } from '@/features/review/case-detail/types'
import { useCaseDetail } from '@/features/review/case-detail/useCaseDetail'
import { EvidenceMeter } from '@/features/review/shared/components/EvidenceMeter'
import { cn } from '@/lib/utils'

type Tab = 'evidence' | 'audit'

/**
 * Page 2 — Case detail (`/cases/:id`), now an Evidence Workspace. Widgets 1–28 per
 * `sprint/00-app-spec.md` § 4 and ADR-0004.
 *
 * Twenty-eight widgets on one screen is deliberate. The contract this workflow is built on is
 * **one screen to resolve one reason**, and splitting the evidence away from the decision
 * breaks it: a reviewer who has to navigate to weigh counter-evidence will decide without it.
 *
 * Composition only lives here. Every piece is its own component under `components/`. What the
 * reviewer is looking at — the open reason, the selected line, the one drawer — lives in the
 * store's `workspace` slice so the matrix, the map, the swimlane and the drawer read one
 * selection; the reviewer's unsaved decision lives in the same store's `drafts`, untouched by
 * any of that, so a refused save still re-renders with their input intact.
 */
export function CaseDetailPage() {
  const { id = '' } = useParams()
  const navigate = useNavigate()
  const {
    status,
    detail,
    error,
    reload,
    audit,
    auditStatus,
    saveStatus,
    saveError,
    conflict,
    save,
  } = useCaseDetail(id)

  const draft = useCaseDetailStore((state) => state.drafts[id]) ?? EMPTY_DRAFT
  const setAction = useCaseDetailStore((state) => state.setAction)
  const clearDraft = useCaseDetailStore((state) => state.clearDraft)
  const workspace = useCaseDetailStore((state) => state.workspace)
  const openCase = useCaseDetailStore((state) => state.openCase)
  const selectReason = useCaseDetailStore((state) => state.selectReason)
  const selectLine = useCaseDetailStore((state) => state.selectLine)
  const openSource = useCaseDetailStore((state) => state.openSource)
  const openComparison = useCaseDetailStore((state) => state.openComparison)

  const [tab, setTab] = useState<Tab>('evidence')
  const [confirmOpen, setConfirmOpen] = useState(false)
  const panelRef = useRef<HTMLDivElement>(null)

  // The screen opens on the strongest reason and on the line that raised it, rather than on a
  // general profile page — `brief/04_DETAIL_KASUS_DISPOSISI.md` § 1. The API already orders
  // reasons strongest-first, so the first card is the one to open. Re-seeded whenever the
  // detail changes, which includes the reload after a version conflict.
  useEffect(() => {
    if (!detail) {
      return
    }
    openCase(detail.case_id, {
      reasonCode: detail.reasons[0]?.code ?? null,
      lineId: primaryLineId(detail),
    })
  }, [detail, openCase])

  const openReason = useMemo(
    () => detail?.reasons.find((reason) => reason.code === workspace.reasonCode) ?? null,
    [detail, workspace.reasonCode],
  )
  const matrix = useMemo(() => (detail ? buildEvidenceMatrix(detail) : null), [detail])

  const templateCaveat = detail?.comparisons.find((entry) => entry.template_caveat)
    ?.template_caveat

  if (status === 'loading') {
    return <CaseDetailLoading />
  }
  if (status === 'failed' || !detail || !matrix) {
    return <CaseDetailFailed error={error} onRetry={reload} />
  }

  const pickAction = (action: DispositionAction) => {
    setAction(id, action)
    panelRef.current?.focus()
  }

  const commit = async () => {
    if (!draft.action) {
      return
    }
    const response = await save({
      action: draft.action,
      structured_reason: draft.structuredReason,
      note: draft.note.trim() || undefined,
      expected_case_version: detail.case_version,
      requested_evidence:
        draft.action === 'REQUEST_EVIDENCE' ? draft.requestedEvidence : undefined,
    })
    if (!response) {
      // Refused. The draft is untouched on purpose — see `store.ts`.
      return
    }
    clearDraft(id)
    // "Minta bukti tambahan" carries the case forward to Ingest; every other action returns to
    // the queue, which still holds the filters and order the reviewer left it on.
    navigate(
      draft.action === 'REQUEST_EVIDENCE'
        ? `/ingest?case=${encodeURIComponent(id)}`
        : '/',
    )
  }

  const requestSave = () => {
    if (draft.action === 'CONFIRM_ANOMALY') {
      setConfirmOpen(true)
      return
    }
    void commit()
  }

  return (
    <PageShell width="full">
      <nav className="mb-[14px] flex items-center gap-[9px] text-meta text-ink-3">
        <Link to="/" className="text-brand underline underline-offset-2">
          Antrean Review
        </Link>
        <span aria-hidden>/</span>
        <span data-numeric className="font-mono">
          {detail.case_id.replace(/^case_/, '').slice(0, 14)}
        </span>
      </nav>

      {conflict ? <VersionConflictBanner conflict={conflict} onReload={reload} /> : null}
      {saveStatus === 'failed' ? (
        <SaveFailedBanner error={saveError} onRetry={requestSave} />
      ) : null}
      {/* Above the header, so it is read before the action buttons inside it. */}
      {templateCaveat ? <TemplateCaveatBanner caveat={templateCaveat} /> : null}

      <CaseHeader detail={detail} onPickAction={pickAction} />

      <div
        role="tablist"
        aria-label="Bagian detail kasus"
        className="mb-[14px] flex w-fit gap-[6px] rounded-md border border-line bg-sunk p-1"
      >
        {(
          [
            ['evidence', 'Bukti & disposisi'],
            ['audit', 'Riwayat audit'],
          ] as const
        ).map(([value, label]) => (
          <button
            key={value}
            type="button"
            role="tab"
            id={`tab-${value}`}
            aria-selected={tab === value}
            aria-controls={`panel-${value}`}
            onClick={() => setTab(value)}
            className={cn(
              'rounded-sm px-4 py-2 text-small font-semibold',
              tab === value ? 'bg-card text-ink shadow-panel' : 'text-ink-2',
            )}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === 'evidence' ? (
        <div
          role="tabpanel"
          id="panel-evidence"
          aria-labelledby="tab-evidence"
          className="grid items-start gap-[14px] lg:grid-cols-[296px_minmax(0,1fr)_348px]"
        >
          <div className="flex flex-col gap-[14px]">
            <ClaimLineList
              lines={detail.lines}
              selectedLineId={workspace.lineId}
              onSelect={selectLine}
            />
            <div className="rounded-lg border border-line bg-card p-[15px] shadow-panel">
              <p className="mb-[9px] font-mono text-micro font-semibold tracking-label text-ink-3">
                KELENGKAPAN BUKTI
              </p>
              <EvidenceMeter completeness={detail.evidence_completeness} />
              {detail.evidence_completeness.missing_reference_count > 0 ? (
                <p className="mt-2 text-meta text-band-conflict">
                  {detail.evidence_completeness.missing_reference_count} rujukan tidak dapat
                  diselesaikan: cacat integritas bukti.
                </p>
              ) : null}
            </div>
          </div>

          {/*
            Reading order in the middle column is binding (display rule 1): the reason cards
            come first, then the matrix, the map and the swimlane that explain them. None of the
            three renders a numeric score.
          */}
          <div className="flex min-w-0 flex-col gap-[14px]">
            {detail.reasons.length === 0 ? (
              <div className="rounded-lg border border-line bg-card p-[18px] shadow-panel">
                <p className="text-body-lg font-medium text-pretty">
                  Tidak ada risiko teramati pada versi mesin ini.
                </p>
                <p className="mt-2 text-small text-ink-2 text-pretty">
                  Tidak ada detektor yang menyala. Ini bukan pernyataan bahwa klaimnya bersih atau
                  aman, hanya bahwa versi mesin ini tidak mengamati apa pun.
                </p>
              </div>
            ) : null}

            {detail.reasons.map((reason, index) => {
              const comparison = comparisonForReason(detail, index)
              return (
                <ReasonCard
                  key={reason.code}
                  reason={reason}
                  isOpen={workspace.reasonCode === reason.code}
                  onToggle={() =>
                    selectReason(workspace.reasonCode === reason.code ? null : reason.code)
                  }
                  sources={detail.sources}
                  onOpenSource={openSource}
                  onCompare={comparison ? () => openComparison(comparison) : null}
                />
              )
            })}

            <EvidenceMatrix
              matrix={matrix}
              sources={detail.sources}
              selectedLineId={workspace.lineId}
              openReasonCode={workspace.reasonCode}
              onSelectLine={selectLine}
              onOpenSource={openSource}
            />

            <EvidenceMap
              detail={detail}
              reason={openReason}
              selectedLineId={workspace.lineId}
              onOpenSource={openSource}
            />

            <EpisodeSwimlane detail={detail} onOpenSource={openSource} />

            {/*
              Last in the column, collapsed, on demand (ADR-0005 § Decision 7). The reasons and
              the evidence are always read first; the briefing is a footnote a reviewer may ask
              for, never a headline the page volunteers.
            */}
            <BriefingPanel caseId={detail.case_id} sources={detail.sources} onOpenSource={openSource} />
          </div>

          <DispositionPanel
            detail={detail}
            saveStatus={saveStatus}
            onSave={requestSave}
            panelRef={panelRef}
          />
        </div>
      ) : (
        <div role="tabpanel" id="panel-audit" aria-labelledby="tab-audit">
          <AuditTimeline caseId={detail.case_id} events={audit} status={auditStatus} />
        </div>
      )}

      <CaseDrawerHost sources={detail.sources} versions={detail.versions} />
      <ConfirmAnomalyDialog
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        structuredReason={draft.structuredReason}
        onConfirm={() => {
          setConfirmOpen(false)
          void commit()
        }}
      />
    </PageShell>
  )
}

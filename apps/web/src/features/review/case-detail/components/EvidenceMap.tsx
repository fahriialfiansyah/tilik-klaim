import type { CSSProperties } from 'react'

import { EvidenceRefButton } from '@/features/review/case-detail/components/EvidenceRefButton'
import { MATRIX_CELL_LABELS, RESOURCE_LABELS } from '@/features/review/case-detail/labels'
import {
  assertSinglePath,
  mapForReason,
  type EvidenceMapModel,
  type MapNode,
} from '@/features/review/case-detail/map'
import type { CaseDetail, EvidenceRef, Reason } from '@/features/review/case-detail/types'
import { cn } from '@/lib/utils'

const MICRO_LABEL = 'font-mono text-micro font-semibold tracking-label text-ink-3'

const NODE_CLASSES: Record<MapNode['state'], string> = {
  FOUND: 'border-line bg-sunk',
  MISSING: 'border-band-signal-line bg-band-signal-bg text-band-signal',
  UNRESOLVED: 'border-band-conflict-line bg-band-conflict-bg text-band-conflict',
}

function caption(node: MapNode): string {
  return node.type === 'Claim' ? 'Klaim' : RESOURCE_LABELS[node.type]
}

function Node({
  node,
  sources,
  onOpenSource,
}: {
  readonly node: MapNode
  readonly sources: CaseDetail['sources']
  readonly onOpenSource: (reference: EvidenceRef) => void
}) {
  return (
    <span className={cn('block rounded-md border px-[13px] py-[9px] text-meta', NODE_CLASSES[node.state])}>
      <span className={cn('block uppercase', MICRO_LABEL)}>{caption(node)}</span>
      {node.reference ? (
        <>
          {/* The line node carries the billed description; a terminal's label is its id, which
              the reference button already says, so it is not repeated. */}
          {node.label !== node.reference.resource_id ? (
            <span className="block font-medium">{node.label}</span>
          ) : null}
          <EvidenceRefButton reference={node.reference} sources={sources} onOpen={onOpenSource} />
        </>
      ) : (
        <span className="block font-medium">
          {node.state === 'MISSING' ? MATRIX_CELL_LABELS.MISSING : node.label}
        </span>
      )}
    </span>
  )
}

function Terminals({
  model,
  sources,
  onOpenSource,
}: {
  readonly model: EvidenceMapModel
  readonly sources: CaseDetail['sources']
  readonly onOpenSource: (reference: EvidenceRef) => void
}) {
  return (
    <ul aria-label="Bukti yang diharapkan" className="flex flex-col gap-2 border-s-2 border-line ps-4">
      {model.terminals.map((node, index) => (
        <li
          key={node.key}
          style={{ '--tk-index': index } as CSSProperties}
          className="tk-enter-fade relative"
        >
          {/*
            Setiap cabang tumbuh keluar dari batang, satu demi satu. Ini bukan hiasan:
            yang digambar adalah rantai bukti yang terbentuk, dan itu persis yang
            dikerjakan produk ini. Simpul yang hilang tetap tergambar dan tetap berhenti
            di tempatnya — geraknya tidak pernah menyiratkan bukti yang tidak ada.
          */}
          <span aria-hidden className="tk-grow-x absolute -start-4 top-1/2 h-px w-4 bg-line" />
          <Node node={node} sources={sources} onOpenSource={onOpenSource} />
        </li>
      ))}
    </ul>
  )
}

/**
 * Widget 15 — the reason-focused Evidence Map (ADR-0004).
 *
 * One trunk — claim → cited line — and terminals hanging off its end, one per expected type
 * and one per cited reference. Terminals never link to each other, so the picture stays a
 * path rather than a network (display rule 3); `assertSinglePath` fails in development the
 * moment that stops being true.
 *
 * The counter-track is drawn on its own labelled branch. It is *in addition to* widget 13,
 * which stays visible in the reason card — display rule 2 gives counter-evidence equal standing,
 * and equal standing is not satisfied by a footnote under the trunk.
 */
export function EvidenceMap({
  detail,
  reason,
  selectedLineId,
  onOpenSource,
}: {
  readonly detail: CaseDetail
  readonly reason: Reason | null
  readonly selectedLineId: string | null
  readonly onOpenSource: (reference: EvidenceRef) => void
}) {
  const model = reason ? mapForReason(detail, reason, selectedLineId) : null
  if (model && import.meta.env.DEV) {
    assertSinglePath(model)
  }

  return (
    <section aria-label="Peta bukti" className="rounded-lg border border-line bg-card p-[18px] shadow-panel">
      <p className="mb-[3px] text-small font-semibold">Peta bukti</p>
      <p className="mb-[14px] text-meta text-ink-3 text-pretty">
        {reason
          ? `Untuk alasan: ${reason.sentence}`
          : 'Belum ada alasan yang ditelusuri. Buka satu kartu alasan untuk melihat peta buktinya.'}
      </p>

      {model ? (
        <div className="grid gap-4 md:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)]">
          <ol aria-label="Jalur klaim" className="flex flex-col gap-2">
            {model.trunk.map((node, index) => (
              <li
                key={node.key}
                style={{ '--tk-index': index } as CSSProperties}
                className="tk-enter relative"
              >
                <Node node={node} sources={detail.sources} onOpenSource={onOpenSource} />
                {index < model.trunk.length - 1 ? (
                  <span aria-hidden className="tk-grow-y mx-auto block h-3 w-px bg-line" />
                ) : null}
              </li>
            ))}
          </ol>

          <div className="flex flex-col gap-4">
            <div>
              <p className={cn('mb-2', MICRO_LABEL)}>BUKTI YANG DIHARAPKAN DI BAWAH BARIS INI</p>
              <Terminals model={model} sources={detail.sources} onOpenSource={onOpenSource} />
            </div>

            <div>
              <p className={cn('mb-2 text-ink-2', MICRO_LABEL)}>BUKTI TANDINGAN: CABANG TERPISAH</p>
              <ul
                aria-label="Bukti tandingan"
                className="flex flex-col gap-2 border-s-2 border-dashed border-line-strong ps-4"
              >
                {model.counter.length === 0 ? (
                  <li className="text-meta text-ink-3">Tidak ada bukti tandingan untuk alasan ini.</li>
                ) : (
                  model.counter.map((note) => (
                    <li key={note.note} className="rounded-md border border-dashed border-line-strong bg-sunk px-[13px] py-[9px]">
                      <p className="text-small leading-relaxed text-pretty">{note.note}</p>
                      {note.refs.length > 0 ? (
                        <p className="mt-1 flex flex-wrap gap-x-3 gap-y-1">
                          {note.refs.map((ref) => (
                            <EvidenceRefButton
                              key={`${ref.resource_type}:${ref.resource_id}`}
                              reference={ref}
                              sources={detail.sources}
                              onOpen={onOpenSource}
                            />
                          ))}
                        </p>
                      ) : null}
                    </li>
                  ))
                )}
              </ul>
            </div>
          </div>
        </div>
      ) : null}

      <p className="mt-[14px] text-meta text-ink-3 text-pretty">
        Satu jalur, bukan jaring hubungan. Simpul ujung tidak saling terhubung; yang tidak punya
        sumber daya pendukung berhenti di sana.
      </p>
    </section>
  )
}

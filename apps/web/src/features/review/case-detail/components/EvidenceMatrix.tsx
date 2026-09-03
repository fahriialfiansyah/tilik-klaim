import { PerfectScrollArea } from '@/components/wrappers/PerfectScrollArea'
import { EvidenceRefButton } from '@/features/review/case-detail/components/EvidenceRefButton'
import {
  MATRIX_CELL_LABELS,
  MATRIX_CELL_MEANINGS,
  RESOURCE_LABELS,
} from '@/features/review/case-detail/labels'
import {
  CLAIM_ROW_KEY,
  type EvidenceMatrix as EvidenceMatrixModel,
  type MatrixCell,
  type MatrixCellState,
  type MatrixRow,
} from '@/features/review/case-detail/matrix'
import type { EvidenceRef, SourceResource } from '@/features/review/case-detail/types'
import { cn } from '@/lib/utils'

const MICRO_LABEL = 'font-mono text-micro font-semibold tracking-label text-ink-3'

/**
 * Each state has a colour **and** a word, and no two words are the same. Red stays reserved
 * for the deterministic defect (`UNRESOLVED`); `MISSING` is a signal, not a conflict — an
 * absent record is an input to a finding, not the finding itself.
 */
const CELL_CLASSES: Record<MatrixCellState, string> = {
  FOUND: 'border-line bg-sunk text-ink-2',
  MISSING: 'border-band-signal-line bg-band-signal-bg text-band-signal',
  UNRESOLVED: 'border-band-conflict-line bg-band-conflict-bg text-band-conflict',
  NOT_EXPECTED: 'border-transparent bg-transparent text-ink-3',
}

function shortCode(code: string): string {
  return code.trim().split(/\s+/).at(-1) ?? code
}

function Cell({
  cell,
  sources,
  onOpenSource,
}: {
  readonly cell: MatrixCell
  readonly sources: readonly SourceResource[]
  readonly onOpenSource: (reference: EvidenceRef) => void
}) {
  // Quiet to the eye, explicit to assistive technology. The dash is not "absent" — the words
  // beside it say nobody expected anything here, which is the whole point of the fourth state.
  if (cell.state === 'NOT_EXPECTED') {
    return (
      <td className="px-3 py-[9px] text-center text-meta text-ink-3" title={MATRIX_CELL_MEANINGS.NOT_EXPECTED}>
        <span aria-hidden>—</span>
        <span className="sr-only">{MATRIX_CELL_LABELS.NOT_EXPECTED}</span>
      </td>
    )
  }
  return (
    <td className="px-3 py-[9px] align-top">
      <span
        title={MATRIX_CELL_MEANINGS[cell.state]}
        className={cn(
          'mb-1 inline-block rounded-sm border px-2 py-[2px] text-meta font-medium',
          CELL_CLASSES[cell.state],
        )}
      >
        {MATRIX_CELL_LABELS[cell.state]}
      </span>
      {cell.refs.length > 0 ? (
        <span className="flex flex-col gap-[2px]">
          {cell.refs.map((ref) => (
            <EvidenceRefButton
              key={`${ref.resource_type}:${ref.resource_id}`}
              reference={ref}
              sources={sources}
              onOpen={onOpenSource}
            />
          ))}
        </span>
      ) : null}
    </td>
  )
}

function RowHeader({
  row,
  isSelected,
  onSelectLine,
}: {
  readonly row: MatrixRow
  readonly isSelected: boolean
  readonly onSelectLine: (lineId: string) => void
}) {
  const reasons = `${row.reasonCodes.length} alasan`
  if (row.line === null) {
    return (
      <th scope="row" className="px-3 py-[9px] text-left align-top font-normal">
        <span className="block text-small font-medium">Tingkat klaim</span>
        <span className="block text-meta text-ink-3">
          alasan yang tidak merujuk baris tertentu · {reasons}
        </span>
      </th>
    )
  }
  return (
    <th scope="row" className="p-0 text-left align-top font-normal">
      <button
        type="button"
        aria-pressed={isSelected}
        onClick={() => onSelectLine(row.line?.line_id ?? '')}
        className={cn(
          'block w-full border-s-[3px] px-3 py-[9px] text-left hover:bg-sunk',
          isSelected ? 'border-s-brand bg-sunk' : 'border-s-transparent',
        )}
      >
        <span className="block text-small font-medium leading-snug">{row.line.description}</span>
        <span data-numeric className="block font-mono text-meta text-ink-3">
          {shortCode(row.line.code)} · {reasons}
        </span>
      </button>
    </th>
  )
}

/**
 * Widget 28 — the Evidence Matrix (ADR-0004).
 *
 * A real `<table>`: lines are rows, expected types are columns, and each cell is one of four
 * states with its own words. A row cited by the open reason is highlighted; the selected line
 * is `aria-pressed`. Every reference opens through `EvidenceRefButton`, so an unresolvable one
 * is flagged as a defect here as it is everywhere else (display rule 4).
 */
export function EvidenceMatrix({
  matrix,
  sources,
  selectedLineId,
  openReasonCode,
  onSelectLine,
  onOpenSource,
}: {
  readonly matrix: EvidenceMatrixModel
  readonly sources: readonly SourceResource[]
  readonly selectedLineId: string | null
  readonly openReasonCode: string | null
  readonly onSelectLine: (lineId: string) => void
  readonly onOpenSource: (reference: EvidenceRef) => void
}) {
  const hasReasons = matrix.columns.length > 0
  const hasLines = matrix.rows.some((row) => row.key !== CLAIM_ROW_KEY)

  return (
    <section
      aria-label="Matriks bukti"
      className="overflow-hidden rounded-lg border border-line bg-card shadow-panel"
    >
      <div className="border-b border-line px-[15px] py-[13px]">
        <p className="text-small font-semibold">Matriks bukti</p>
        <p className="mt-[2px] text-meta text-ink-3">
          Baris tagihan terhadap jenis bukti yang diharapkan. Sel kosong berarti tidak ada yang
          diharapkan — bukan tidak ada.
        </p>
      </div>

      {!hasLines ? (
        <p className="px-[15px] py-6 text-small text-ink-3">
          Bundel ini tidak memuat baris tagihan yang dapat ditampilkan.
        </p>
      ) : !hasReasons ? (
        <p className="px-[15px] py-6 text-small text-ink-3 text-pretty">
          Tidak ada risiko teramati pada versi mesin ini, sehingga tidak ada jenis bukti yang
          diharapkan untuk dipetakan. Ini bukan pernyataan tentang klaimnya.
        </p>
      ) : (
        <PerfectScrollArea axis="both" className="max-w-full">
          <table aria-label="Matriks bukti" className="w-full border-collapse text-small">
            <thead>
              <tr className="bg-sunk">
                <th scope="col" className={cn('px-3 py-2 text-left', MICRO_LABEL)}>
                  BARIS
                </th>
                {/* CSS uppercase, not a transformed string: screen readers read the words. */}
                {matrix.columns.map((type) => (
                  <th key={type} scope="col" className={cn('px-3 py-2 text-left uppercase', MICRO_LABEL)}>
                    {RESOURCE_LABELS[type]}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {matrix.rows.map((row) => {
                const isCitedByOpenReason =
                  openReasonCode !== null && row.reasonCodes.includes(openReasonCode)
                return (
                  <tr
                    key={row.key}
                    className={cn('border-t border-line', isCitedByOpenReason && 'bg-brand-soft/40')}
                  >
                    <RowHeader
                      row={row}
                      isSelected={row.line !== null && row.line.line_id === selectedLineId}
                      onSelectLine={onSelectLine}
                    />
                    {row.cells.map((cell) => (
                      <Cell key={cell.type} cell={cell} sources={sources} onOpenSource={onOpenSource} />
                    ))}
                  </tr>
                )
              })}
            </tbody>
          </table>
        </PerfectScrollArea>
      )}
    </section>
  )
}

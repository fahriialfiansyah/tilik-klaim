import { RESOURCE_LABELS } from '@/features/review/case-detail/labels'
import { findSource } from '@/features/review/case-detail/components/EvidenceRefButton'
import type {
  CaseDetail,
  ClaimLineView,
  EvidenceRef,
  Reason,
  SourceResource,
} from '@/features/review/case-detail/types'
import { cn } from '@/lib/utils'

type PathNode = {
  readonly key: string
  readonly caption: string
  readonly label: string
  readonly reference: EvidenceRef | null
  readonly isDeadEnd: boolean
}

/**
 * Build the single track from claim to the clinical evidence that should sit under one line.
 *
 * Display rule 3 (`sprint/00-app-spec.md` § 4): **one path, not a network.** Every node has at
 * most one successor by construction here — there is no branching to draw, and if this ever
 * starts to look like a web the design is wrong rather than the renderer. The chain stops at
 * the first node with nothing under it, which is exactly the finding a phantom reason makes.
 */
function buildPath(
  detail: CaseDetail,
  line: ClaimLineView | null,
  reason: Reason | null,
  sources: readonly SourceResource[],
): readonly PathNode[] {
  const nodes: PathNode[] = [
    {
      key: 'claim',
      caption: 'Klaim',
      label: detail.case_id.replace(/^case_/, '').slice(0, 10),
      reference: null,
      isDeadEnd: false,
    },
  ]

  if (line) {
    nodes.push({
      key: 'line',
      caption: RESOURCE_LABELS.ClaimLine,
      label: line.description,
      reference: { resource_type: 'ClaimLine', resource_id: line.line_id, label: line.line_id },
      isDeadEnd: false,
    })
  }

  const encounter = reason?.evidence.find((ref) => ref.resource_type === 'Encounter')
  if (encounter) {
    nodes.push({
      key: 'encounter',
      caption: RESOURCE_LABELS.Encounter,
      label: encounter.resource_id,
      reference: encounter,
      isDeadEnd: false,
    })
  }

  // With no reason selected there is no trail to follow, and no claim to make about what is
  // missing. Marking the chain as a dead end here said "bukti klinis tidak ditemukan" on a case
  // where every line was supported and nothing had fired — an accusation the data does not make.
  if (reason === null) {
    return nodes
  }

  // The clinical evidence the line should rest on: whatever the reason cites that is not the
  // claim, the line, or the visit. Absent means the chain stops, and that is the point.
  const clinical = reason.evidence.find(
    (ref) => !['Claim', 'ClaimLine', 'Encounter'].includes(ref.resource_type),
  )
  if (clinical) {
    const source = findSource(sources, clinical)
    nodes.push({
      key: 'clinical',
      caption: RESOURCE_LABELS[clinical.resource_type],
      label: clinical.resource_id,
      reference: clinical,
      isDeadEnd: source === null || source.availability === 'MISSING',
    })
    return nodes
  }

  nodes.push({
    key: 'clinical-missing',
    caption: 'Bukti klinis',
    label: 'tidak ditemukan',
    reference: null,
    isDeadEnd: true,
  })
  return nodes
}

/** Widget 15 — the evidence path for the selected line, kept small and single-track. */
export function EvidencePath({
  detail,
  line,
  reason,
  sources,
  onOpenSource,
}: {
  readonly detail: CaseDetail
  readonly line: ClaimLineView | null
  readonly reason: Reason | null
  readonly sources: readonly SourceResource[]
  readonly onOpenSource: (reference: EvidenceRef) => void
}) {
  const nodes = buildPath(detail, line, reason, sources)

  return (
    <section
      aria-label="Jalur bukti"
      className="rounded-lg border border-line bg-card p-[18px] shadow-panel"
    >
      <p className="mb-[14px] text-small font-semibold">
        Jalur bukti{line ? ` — ${line.description}` : ''}
      </p>

      <ol className="flex flex-wrap items-center gap-y-2">
        {nodes.map((node, index) => (
          <li key={node.key} className="flex items-center">
            {node.reference ? (
              <button
                type="button"
                onClick={() => onOpenSource(node.reference as EvidenceRef)}
                className={cn(
                  'rounded-md border px-[13px] py-[9px] text-left text-meta hover:border-brand',
                  node.isDeadEnd
                    ? 'border-band-signal-line bg-band-signal-bg text-band-signal'
                    : 'border-line bg-sunk',
                )}
              >
                <span className="block text-micro text-ink-3">{node.caption}</span>
                <span data-numeric className="block font-medium">
                  {node.label}
                </span>
              </button>
            ) : (
              <span
                className={cn(
                  'rounded-md border px-[13px] py-[9px] text-meta',
                  node.isDeadEnd
                    ? 'border-band-signal-line bg-band-signal-bg text-band-signal'
                    : 'border-line bg-sunk',
                )}
              >
                <span className="block text-micro text-ink-3">{node.caption}</span>
                <span className="block font-medium">{node.label}</span>
              </span>
            )}
            {index < nodes.length - 1 ? (
              <span aria-hidden className="mx-[3px] w-[22px] text-center text-ink-3">
                →
              </span>
            ) : null}
          </li>
        ))}
      </ol>

      <p className="mt-[14px] text-meta text-ink-3 text-pretty">
        {reason === null
          ? 'Belum ada alasan yang ditelusuri. Buka satu kartu alasan untuk melihat jalur buktinya.'
          : 'Satu jalur, bukan jaring hubungan. Rantai berhenti di simpul yang tidak punya sumber daya pendukung.'}
      </p>
    </section>
  )
}

import { cn } from '@/lib/utils'
import type { EvidenceCompleteness } from '@/features/review/shared/types'

const SEGMENTS = 3

/**
 * How much of the expected supporting evidence was present.
 *
 * Deliberately never green: a complete file means the record can be *judged*, not that the claim
 * is sound. `design/DESIGN.md` reserves green for completed, validated actions.
 *
 * Three outcomes, kept apart on purpose — two of them are "we cannot say", and drawing either as
 * a full meter would claim support the screening never found:
 *
 *   - the bundle is incomplete → the record is too thin to judge, which lowers certainty and
 *     points at requesting evidence, never at concluding anything;
 *   - no billed lines were counted → there was nothing to assess;
 *   - otherwise → n of m billed lines carried support.
 */
export function EvidenceMeter({ completeness }: { readonly completeness: EvidenceCompleteness }) {
  const { supported_lines, total_lines, bundle_complete } = completeness

  const assessable = bundle_complete && total_lines > 0
  const filled = assessable ? Math.round((supported_lines / total_lines) * SEGMENTS) : 0

  const label = !bundle_complete
    ? 'Berkas belum lengkap'
    : total_lines === 0
      ? 'Tidak ada baris tertagih'
      : `${supported_lines}/${total_lines} baris didukung`

  return (
    <span className={cn('flex items-center gap-[7px] text-small', assessable ? 'text-ink-2' : 'text-ink-3')}>
      <span aria-hidden className="flex gap-[2px]">
        {Array.from({ length: SEGMENTS }, (_, index) => (
          <span
            key={index}
            className={cn(
              'h-[11px] w-[4px] rounded-sm',
              index < filled ? 'bg-ink-2' : 'bg-line-strong',
            )}
          />
        ))}
      </span>
      {label}
    </span>
  )
}

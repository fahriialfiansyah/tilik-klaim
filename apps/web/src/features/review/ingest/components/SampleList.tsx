import type { SampleSummary } from '@/features/review/ingest/types'
import { cn } from '@/lib/utils'

/**
 * Which risk mode each scenario is there to demonstrate — colour *and* the label beside it.
 *
 * The clean scenario is deliberately neutral rather than green. Green is reserved for a
 * completed, validated action, and a claim that no detector fired on is not "safe" — it is a
 * claim on which nothing was observed.
 */
const SCENARIO_DOT: Record<string, string> = {
  clean: 'bg-band-quiet',
  phantom: 'bg-band-conflict',
  repeat: 'bg-band-conflict',
  clone: 'bg-band-context',
  unbundled: 'bg-band-conflict',
}

/**
 * Widget 3 — the five curated scenarios, loaded without an upload.
 *
 * The rows say when a scenario carries a prior claim. Repeat billing, cloned documentation, and
 * unbundling are only visible *across* claims, so those three submit a history bundle before
 * their own — and a demo that ingested two bundles while appearing to ingest one would be
 * quietly misrepresenting how the detector works.
 */
export function SampleList({
  samples,
  activeScenario,
  onPick,
  isBusy,
}: {
  readonly samples: readonly SampleSummary[]
  readonly activeScenario: string | null
  readonly onPick: (scenario: string) => void
  readonly isBusy: boolean
}) {
  return (
    <div>
      <p className="mt-[18px] mb-2 font-mono text-micro font-semibold tracking-label text-ink-3">
        ATAU PAKAI KASUS CONTOH
      </p>

      {samples.length === 0 ? (
        <p className="rounded-md border border-line bg-sunk px-3 py-[10px] text-small text-ink-3">
          Daftar kasus contoh tidak dapat dimuat. Unggah berkas sendiri masih bisa dilakukan.
        </p>
      ) : null}

      <ul>
        {samples.map((sample) => (
          <li key={sample.scenario} className="mb-[6px]">
            <button
              type="button"
              disabled={isBusy}
              aria-pressed={activeScenario === sample.scenario}
              onClick={() => onPick(sample.scenario)}
              className={cn(
                'flex w-full items-center justify-between gap-3 rounded-md border px-3 py-[10px] text-left disabled:opacity-60',
                activeScenario === sample.scenario
                  ? 'border-brand bg-brand-soft'
                  : 'border-line bg-card hover:border-line-strong hover:bg-sunk',
              )}
            >
              <span className="flex min-w-0 items-center gap-[10px]">
                <span
                  aria-hidden
                  className={cn(
                    'size-2 shrink-0 rounded-sm',
                    SCENARIO_DOT[sample.scenario] ?? 'bg-line-strong',
                  )}
                />
                <span className="min-w-0">
                  <span className="block text-small font-semibold">{sample.label}</span>
                  <span className="block text-meta text-ink-3 text-pretty">
                    {sample.description}
                  </span>
                </span>
              </span>
              <span className="shrink-0 text-end">
                {sample.history_count > 0 ? (
                  <span className="block text-meta text-ink-3">
                    + {sample.history_count} klaim riwayat
                  </span>
                ) : null}
                <span data-numeric className="block font-mono text-micro text-ink-3">
                  {sample.scenario}
                </span>
              </span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}

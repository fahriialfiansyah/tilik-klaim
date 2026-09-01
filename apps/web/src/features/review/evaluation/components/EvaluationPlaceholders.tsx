import { AlertTriangle, FlaskConical, RotateCw } from 'lucide-react'

import { Button } from '@/components/ui/button'

const SKELETON_ROWS = 4

/** The command that produces a run. Shown verbatim so it can be copied and pasted. */
export const RUN_COMMAND =
  'cd evaluation && uv run python -m runner.run --build ../packages/data/build'

export function EvaluationLoading() {
  return (
    <div className="space-y-3 p-4" aria-busy="true" aria-live="polite">
      <span className="sr-only">Memuat hasil evaluasi…</span>
      {Array.from({ length: SKELETON_ROWS }, (_, index) => (
        <div key={index} className="h-[52px] animate-pulse rounded-md bg-line" />
      ))}
    </div>
  )
}

/**
 * Widget 9 — no evaluation has been run.
 *
 * `sprint/00-app-spec.md` § 6 rule 4: **belum ada evaluasi ≠ nol**. This state renders no metric
 * at all, not a table of zeros — a zero would say the evaluation ran and found nothing, which is
 * the opposite of what happened. It also names the command, because the next action here is a
 * command someone runs, not a button on this page.
 */
export function NoEvaluationRun() {
  return (
    <section className="rounded-md border border-line bg-card px-8 py-[54px] text-center">
      <div className="mb-[18px] flex justify-center text-ink-3">
        <FlaskConical aria-hidden="true" className="h-8 w-8" />
      </div>
      <p className="mb-2 text-lead font-semibold text-ink">Belum ada evaluasi yang dijalankan</p>
      <p className="mx-auto mb-5 max-w-[520px] text-body-lg text-ink-2 text-pretty">
        Halaman ini hanya menampilkan artefak yang sudah dihasilkan. Evaluasi dijalankan luring
        oleh seorang teknisi terhadap partisi uji yang dibekukan — bukan dari halaman ini, dan
        bukan dari sebuah tombol.
      </p>
      <pre className="mx-auto max-w-[560px] overflow-x-auto rounded-md bg-sunk px-4 py-3 text-left text-small font-mono text-ink">
        <code>{RUN_COMMAND}</code>
      </pre>
    </section>
  )
}

/** The service did not answer. Distinct from "no run yet", and offering a different next step. */
export function EvaluationFailed({ onRetry }: { readonly onRetry: () => void }) {
  return (
    <section className="rounded-md border border-line bg-card px-8 py-[54px] text-center">
      <div className="mb-[18px] flex justify-center text-band-conflict">
        <AlertTriangle aria-hidden="true" className="h-8 w-8" />
      </div>
      <p className="mb-2 text-lead font-semibold text-ink">Hasil evaluasi tidak dapat dimuat</p>
      <p className="mx-auto mb-5 max-w-[520px] text-body-lg text-ink-2 text-pretty">
        Layanan tidak menjawab. Ini berbeda dari “belum ada evaluasi”: artefaknya mungkin ada,
        tetapi tidak terbaca dari sini.
      </p>
      <Button variant="outline" onClick={onRetry}>
        <RotateCw aria-hidden="true" className="mr-1 h-3 w-3" />
        Coba lagi
      </Button>
    </section>
  )
}

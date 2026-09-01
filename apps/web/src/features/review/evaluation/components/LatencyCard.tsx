import { formatLatency } from '@/features/review/evaluation/format'

/**
 * Widget 7 — screening latency.
 *
 * Labelled as a prototype measurement, because that is what it is. `docs/canonical/06_evaluation_plan.md`
 * lists latency under "demonstrates prototype latency and workflow can be measured" and under
 * "does not demonstrate scale under national production load"; showing the number without that
 * distinction invites the second reading.
 */
export function LatencyCard({
  p50,
  p95,
}: {
  readonly p50: number
  readonly p95: number
}) {
  return (
    <section
      aria-labelledby="latency-heading"
      className="rounded-md border border-line bg-card p-4"
    >
      <h3 id="latency-heading" className="text-body-lg font-semibold text-ink">
        Waktu pemrosesan
      </h3>
      <p className="mb-3 text-micro text-ink-2">
        Waktu penyaringan satu berkas klaim pada mesin pengembangan. Bukan angka produksi dan
        tidak menyatakan apa pun tentang beban skala nasional. Nilai dibulatkan ke milidetik
        penuh, sehingga p50 dan p95 dapat tampak sama pada penyaringan yang sangat cepat; angka
        penuhnya ada di <code className="font-mono">latency.json</code> milik run ini.
      </p>
      <dl className="flex gap-8">
        <div>
          <dt className="text-micro text-ink-2">Nilai tengah (p50)</dt>
          <dd className="font-mono text-lead tabular-nums text-ink">{formatLatency(p50)}</dd>
        </div>
        <div>
          <dt className="text-micro text-ink-2">Persentil 95 (p95)</dt>
          <dd className="font-mono text-lead tabular-nums text-ink">{formatLatency(p95)}</dd>
        </div>
      </dl>
    </section>
  )
}

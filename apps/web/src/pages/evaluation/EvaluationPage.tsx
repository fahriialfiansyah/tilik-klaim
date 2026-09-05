import { LatencyCard } from '@/features/review/evaluation/components/LatencyCard'
import { LimitationsCard } from '@/features/review/evaluation/components/LimitationsCard'
import { MetricBarChart } from '@/features/review/evaluation/components/MetricBarChart'
import { MetricTable } from '@/features/review/evaluation/components/MetricTable'
import { SyntheticBadge } from '@/features/review/evaluation/components/SyntheticBadge'
import { VersionCard } from '@/features/review/evaluation/components/VersionCard'
import {
  EvaluationFailed,
  EvaluationLoading,
  NoEvaluationRun,
} from '@/features/review/evaluation/components/EvaluationPlaceholders'
import {
  BASELINE_COLUMNS,
  MODE_COLUMNS,
  baselineRows,
  falsePositiveChartRows,
  modeRows,
  precisionAtBudgetChartRows,
} from '@/features/review/evaluation/selectors'
import { useEvaluation } from '@/features/review/evaluation/useEvaluation'
import { PageHeader, PageShell } from '@/components/layouts/PageShell'

/**
 * Page 4 — Audit & evaluation (`/evaluation`). Widgets 1–9 per `sprint/00-app-spec.md` § 6.
 *
 * **Display only.** There is no threshold control, no what-if input, and no button that starts a
 * run — rule 1, and it is a safety property rather than a scope cut. A page that could re-tune a
 * threshold would let someone tune against the frozen test set, which invalidates every number
 * the same page is showing.
 *
 * The limitations card renders inside the same branch as the metrics, so no code path can show a
 * number without it (rule 3).
 */
export function EvaluationPage() {
  const { status, data, reload } = useEvaluation()

  return (
    <PageShell>
      <PageHeader
        eyebrow="ARTEFAK EVALUASI · HANYA BACA"
        title="Audit & Evaluasi"
        lede="Bukti terukur dari artefak evaluasi, beserta keterbatasannya. Halaman ini hanya membaca: tidak ada penyetelan ambang batas dan tidak ada eksperimen langsung."
      />

      <div className="space-y-4">
        {status === 'loading' ? <EvaluationLoading /> : null}
        {status === 'absent' ? <NoEvaluationRun /> : null}
        {status === 'failed' ? <EvaluationFailed onRetry={reload} /> : null}

        {status === 'ready' && data ? (
          <>
            <SyntheticBadge dataClass={data.data_class} />
            <VersionCard evaluation={data} />

            <section
              aria-labelledby="baselines-heading"
              className="rounded-md border border-line bg-card p-4"
            >
              <h2 id="baselines-heading" className="mb-1 text-lead font-semibold text-ink">
                Perbandingan baseline
              </h2>
              <p className="mb-3 text-micro text-ink-2">
                Empat pendekatan pada partisi uji yang sama. Lapisan statistik hanya layak
                dipertahankan bila memberi peningkatan terukur atas pendekatan aturan saja.
              </p>
              <MetricTable
                caption="Perbandingan empat baseline"
                columns={BASELINE_COLUMNS}
                rows={baselineRows(data)}
              />
            </section>

            <section
              aria-labelledby="per-mode-heading"
              className="rounded-md border border-line bg-card p-4"
            >
              <h2 id="per-mode-heading" className="mb-1 text-lead font-semibold text-ink">
                Metrik per mode risiko
              </h2>
              <p className="mb-3 text-micro text-ink-2">
                Angka pendekatan hibrida untuk keempat mode. Mode tanpa contoh pada partisi uji
                ditandai tidak terukur, bukan nol.
              </p>
              <MetricTable
                caption="Ketepatan, keterpanggilan, dan F1 per mode risiko"
                columns={MODE_COLUMNS}
                rows={modeRows(data)}
              />
            </section>

            <div className="grid gap-4 lg:grid-cols-2">
              <MetricBarChart
                title="Positif palsu per 100 klaim bersih"
                subtitle="Semakin rendah, semakin sedikit beban tinjauan yang terbuang"
                rows={falsePositiveChartRows(data)}
              />
              <MetricBarChart
                title="Ketepatan pada kapasitas review"
                subtitle="Bagian kasus yang ditinjau yang benar-benar memuat pola yang disuntikkan"
                rows={precisionAtBudgetChartRows(data)}
              />
            </div>

            <LatencyCard p50={data.latency_p50_ms} p95={data.latency_p95_ms} />
            <LimitationsCard limitations={data.limitations} />
          </>
        ) : null}
      </div>
    </PageShell>
  )
}

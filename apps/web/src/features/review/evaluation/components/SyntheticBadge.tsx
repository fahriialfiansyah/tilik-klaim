/**
 * Widget 2 — the synthetic-data badge.
 *
 * Prominent by design, and never conditional. Every number on this page was produced from
 * records this project generated; a reader who misses that will read a prevalence into a figure
 * that is a test-design choice. The badge reads the `data_class` the API sent rather than being
 * hardcoded, so it cannot say "synthetic" about a run that claimed otherwise.
 */
export function SyntheticBadge({ dataClass }: { readonly dataClass: string }) {
  return (
    <p
      className="mb-4 rounded-md border border-notice-line bg-notice-bg px-4 py-3 text-body-lg text-ink"
      role="note"
    >
      <span className="mr-2 rounded-sm bg-ink px-2 py-[2px] text-micro font-semibold uppercase tracking-wide text-card">
        Data {dataClass === 'synthetic' ? 'sintetik' : dataClass}
      </span>
      Seluruh angka di halaman ini berasal dari data sintetik yang dibuat oleh proyek ini. Angka
      di sini <strong>bukan</strong> perkiraan prevalensi, biaya, atau perilaku fasilitas nyata.
    </p>
  )
}

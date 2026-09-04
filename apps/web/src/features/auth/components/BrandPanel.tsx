import { useEffect, useState } from 'react'

import { TilikKlaimMark } from '@/components/brand/TilikKlaimMark'

/**
 * The left half of `/login`: the mark at size, on the same dark navy the app header uses.
 *
 * The mark is an evidence chain closing into a loop, and it draws itself once on load — the
 * solid arc strokes in over ~700 ms, then the amber dashed arc follows. That is motion that
 * *means* the thing the product does; `design/DESIGN.md` locks the direction against "gradien
 * neon atau efek chatbot", and an animation carrying an idea is not the same as ornament.
 *
 * It respects `prefers-reduced-motion`: when reduced motion is requested the mark is simply
 * there, complete, from the first frame. No fallback shimmer, no shortened version.
 */
const DRAW_MS = 700

export function BrandPanel() {
  const [drawn, setDrawn] = useState(false)

  useEffect(() => {
    const reduced = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false
    if (reduced) {
      setDrawn(true)
      return
    }
    // One frame later, so the browser has painted the undrawn state to transition *from*.
    const handle = window.requestAnimationFrame(() => setDrawn(true))
    return () => window.cancelAnimationFrame(handle)
  }, [])

  return (
    <section
      aria-labelledby="brand-heading"
      className="flex flex-col justify-between gap-10 bg-head px-8 py-10 lg:px-12 lg:py-14"
    >
      <div className="flex items-center gap-[10px]">
        <span className="text-lead font-semibold tracking-[.11em] text-ink-inv">TILIKKLAIM</span>
      </div>

      <div className="flex flex-col items-start gap-8">
        <div data-drawn={drawn} data-testid="brand-mark">
          <TilikKlaimMark
            className="block size-[132px] lg:size-[168px]"
            drawn={drawn}
            drawMs={DRAW_MS}
          />
        </div>

        <div className="max-w-[36ch]">
          <h1 id="brand-heading" className="text-page font-semibold text-ink-inv text-pretty">
            Lapisan integritas bukti klaim
          </h1>
          <p className="mt-3 text-body-lg leading-[1.55] text-ink-inv-2 text-pretty">
            Memeriksa apakah setiap baris yang ditagihkan punya bukti klinis yang konsisten,
            lalu menyerahkan keputusannya kepada petugas — bukan kepada mesin.
          </p>
        </div>
      </div>

      <p className="max-w-[44ch] text-meta leading-[1.5] text-ink-inv-2">
        Prototipe fungsional. Seluruh data sintetik, dibangkitkan oleh kode proyek ini; tidak ada
        rekam medis nyata yang terlibat.
      </p>
    </section>
  )
}

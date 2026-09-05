import { useEffect, useRef, useState } from 'react'

import { MOTION } from '@/modules/motion/timing'
import { useReducedMotion } from '@/modules/motion/useReducedMotion'

const DONE = 1

/** Perlambatan di ujung, sehingga angka mendarat pada nilainya alih-alih berhenti mendadak. */
function easeOut(progress: number): number {
  return DONE - (DONE - progress) ** 3
}

/**
 * Menghitung naik ke `value` **satu kali saja**, saat pertama kali tampil.
 *
 * "Satu kali saja" adalah syaratnya, bukan penyederhanaan. Kartu metrik antrean juga
 * berfungsi sebagai saringan: menekannya mengubah angkanya. Kalau angka berdetak ulang
 * setiap kali saringan berubah, mata pembaca ditarik kembali ke skor pada setiap
 * interaksi — persis yang dilarang uji keterpahaman di `design/DESIGN.md`, yang menuntut
 * kalimat alasan yang lebih dulu terbaca.
 *
 * Sesudah detakan itu selesai, hook meneruskan `value` **apa adanya**. Nilai baru dari
 * saringan tampil seketika dan tepat; yang tidak diulang adalah geraknya, bukan datanya.
 */
export function useCountUp(value: number): number {
  const isReduced = useReducedMotion()
  const [progress, setProgress] = useState(isReduced ? DONE : 0)
  const hasCounted = useRef(false)

  useEffect(() => {
    if (hasCounted.current || isReduced) {
      hasCounted.current = true
      setProgress(DONE)
      return
    }
    hasCounted.current = true

    let frame = 0
    const start = performance.now()
    const step = (now: number) => {
      const elapsed = Math.min(DONE, (now - start) / MOTION.count)
      setProgress(elapsed)
      if (elapsed < DONE) {
        frame = requestAnimationFrame(step)
      }
    }
    frame = requestAnimationFrame(step)
    return () => cancelAnimationFrame(frame)
  }, [isReduced])

  return progress >= DONE ? value : Math.round(value * easeOut(progress))
}

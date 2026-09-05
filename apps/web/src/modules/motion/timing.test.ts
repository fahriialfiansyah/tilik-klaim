import { readFileSync } from 'node:fs'

import { describe, expect, test } from 'vitest'

import { MOTION } from '@/modules/motion/timing'

/**
 * Dibaca dari berkas, bukan diimpor: Vitest men-stub impor CSS, dan `?raw` — yang dipakai
 * pengujian lain di proyek ini untuk modul TypeScript — tidak berlaku untuk stylesheet.
 * Jalur relatif terhadap akar paket, tempat Vitest dijalankan.
 */
const CSS = readFileSync('src/styles/motion.css', 'utf8')

/**
 * `MOTION` menduplikasi custom property di `motion.css` karena animasi JavaScript tidak
 * bisa membaca nilai CSS tanpa memaksa layout. Duplikasi itu boleh ada; yang tidak boleh
 * adalah ia menyimpang diam-diam — durasi yang dinaikkan di CSS lalu tidak ikut naik di
 * TypeScript menghasilkan dua kecepatan pada satu layar, dan tidak ada yang gagal.
 */
function cssDuration(name: string): number | null {
  const found = new RegExp(`--motion-${name}:\\s*(\\d+)ms`).exec(CSS)
  return found ? Number(found[1]) : null
}

describe('durasi gerak sama di CSS dan TypeScript', () => {
  test.each(Object.keys(MOTION))('--motion-%s cocok dengan MOTION.%s', (name) => {
    expect(cssDuration(name), `--motion-${name} tidak ada di motion.css`).toBe(
      MOTION[name as keyof typeof MOTION],
    )
  })

  test('setiap --motion-* di CSS punya pasangan di MOTION', () => {
    const declared = [...CSS.matchAll(/--motion-([a-z]+):/g)].map((match) => match[1])
    expect(new Set(declared)).toEqual(new Set(Object.keys(MOTION)))
  })

  test('tidak ada durasi yang melampaui batas alat operasional', () => {
    // design/DESIGN.md mengunci kesan "tenang" untuk alat yang dipakai sepanjang hari.
    // Gerak di atas 400ms berhenti terasa responsif dan mulai terasa sebagai penundaan.
    for (const [name, ms] of Object.entries(MOTION)) {
      expect(ms, name).toBeLessThanOrEqual(400)
    }
  })
})

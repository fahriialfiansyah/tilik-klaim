import { readFileSync } from 'node:fs'

import { describe, expect, test } from 'vitest'

import appHeaderSource from '@/components/layouts/AppHeader?raw'
import caseHeaderSource from '@/features/review/case-detail/components/CaseHeader?raw'
import metricCardsSource from '@/features/review/queue/components/QueueMetricCards?raw'
import barChartSource from '@/features/review/evaluation/components/MetricBarChart?raw'

const MOTION_CSS = readFileSync('src/styles/motion.css', 'utf8')

/** Setiap kelas gerak yang diperkenalkan lapisan ini, plus utility animasi Tailwind. */
const MOTION_CLASS = /\b(tk-enter|tk-enter-fade|tk-grow-x|tk-grow-y|animate-[a-z]+)\b/

/**
 * Baris JSX yang memuat teks badge, beserta baris pembuka elemennya. Cukup untuk melihat
 * `className` yang menempel padanya tanpa mengurai berkas jadi pohon sintaks.
 */
function badgeMarkup(source: string): string {
  const lines = source.split('\n')
  const at = lines.findIndex((line) => line.includes('DATA SINTETIK') && !line.trim().startsWith('*'))
  expect(at, 'badge DATA SINTETIK tidak ditemukan').toBeGreaterThan(-1)
  return lines.slice(Math.max(0, at - 4), at + 1).join('\n')
}

describe('badge DATA SINTETIK tidak pernah bergerak', () => {
  // design/DESIGN.md: badge ini wajib terlihat di setiap halaman dan tidak dapat ditutup.
  // Penanda tata kelola yang memudar masuk, berdenyut, atau meluncur berhenti terbaca
  // sebagai pernyataan permanen dan mulai terbaca sebagai notifikasi yang akan berlalu.
  test.each([
    ['AppHeader', appHeaderSource],
    ['CaseHeader', caseHeaderSource],
  ])('%s memasang badge tanpa kelas gerak', (_name, source) => {
    expect(badgeMarkup(source)).not.toMatch(MOTION_CLASS)
  })
})

describe('tidak ada gerak yang berulang di mana pun', () => {
  // Merah hanya menandai konflik deterministik. Apa pun yang berdenyut atau berkedip
  // berhenti menandai konflik dan mulai terbaca sebagai alarm — atau sebagai tuduhan.
  test('motion.css tidak mendeklarasikan animasi tak berujung', () => {
    expect(MOTION_CSS).not.toMatch(/\binfinite\b/)
  })

  test('kartu metrik tidak memakai animate-pulse atau animate-ping', () => {
    expect(metricCardsSource).not.toMatch(/animate-(pulse|ping|bounce)/)
  })

  test('rel pita dan lencana pita tidak membawa kelas gerak sendiri', () => {
    const railLine = metricCardsSource
      .split('\n')
      .find((line) => line.includes('card.accent'))
    expect(railLine, 'rel pita tidak ditemukan').toBeDefined()
    expect(railLine).not.toMatch(MOTION_CLASS)
  })
})

describe('sakelar prefers-reduced-motion berlaku menyeluruh', () => {
  test('ada blok @media yang mematikan animasi dan transisi', () => {
    expect(MOTION_CSS).toMatch(/@media\s*\(prefers-reduced-motion:\s*reduce\)/)
    expect(MOTION_CSS).toMatch(/animation-duration:\s*0\.01ms\s*!important/)
    expect(MOTION_CSS).toMatch(/transition-duration:\s*0\.01ms\s*!important/)
  })

  test('sakelar itu menjangkau setiap elemen, bukan daftar kelas tertentu', () => {
    const block = MOTION_CSS.slice(MOTION_CSS.indexOf('@media (prefers-reduced-motion'))
    expect(block).toMatch(/\*,\s*\n\s*\*::before,\s*\n\s*\*::after/)
  })
})

describe('bilah metrik tidak bisa berselisih dengan angkanya', () => {
  // sprint/00-app-spec.md § 6 aturan 2: bilah yang tidak sesuai tabel adalah cacat
  // integritas. Karena itu yang dianimasikan transform, dan lebarnya tetap dihitung
  // dari nilai yang sama dengan yang dicetak.
  test('lebar bilah tetap ditulis dari barShare, bukan dari keadaan animasi', () => {
    expect(barChartSource).toMatch(/width:\s*`\$\{barShare\(row\.value, ceiling\) \* PERCENT\}%`/)
  })

  test('yang dianimasikan transform, bukan width', () => {
    expect(barChartSource).toMatch(/tk-grow-x/)
    expect(MOTION_CSS).toMatch(/\.tk-grow-x\s*\{[^}]*transform-origin/)
    // Tidak ada transisi lebar di seluruh lapisan gerak: itu memicu layout per bingkai
    // dan membuka celah antara yang digambar dan yang dicetak.
    expect(MOTION_CSS).not.toMatch(/transition:\s*width/)
  })
})

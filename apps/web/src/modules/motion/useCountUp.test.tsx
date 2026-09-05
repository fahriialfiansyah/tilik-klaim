import { render, screen } from '@testing-library/react'
import { act } from 'react'
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest'

import { MOTION } from '@/modules/motion/timing'
import { useCountUp } from '@/modules/motion/useCountUp'

function Counter({ value }: { readonly value: number }) {
  return <output>{useCountUp(value)}</output>
}

function shown(): number {
  return Number(screen.getByRole('status').textContent)
}

/** Menjalankan animasi sampai tuntas: rAF di jsdom tidak berjalan sendiri. */
function runToCompletion() {
  act(() => {
    vi.advanceTimersByTime(MOTION.count * 2)
  })
}

describe('useCountUp', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  test('mendarat tepat pada nilainya, bukan pada pembulatan di dekatnya', () => {
    render(<Counter value={29} />)
    runToCompletion()

    expect(shown()).toBe(29)
  })

  test('benar-benar melewati nilai antara, bukan melompat ke akhir', () => {
    render(<Counter value={100} />)
    act(() => {
      vi.advanceTimersByTime(MOTION.count / 2)
    })

    // Kalau hook melompat, ini 100. Kalau rAF tidak jalan sama sekali, ini 0.
    // Keduanya berarti tidak ada detakan yang benar-benar terjadi.
    expect(shown()).toBeGreaterThan(0)
    expect(shown()).toBeLessThan(100)
  })

  test('nilai baru tampil seketika dan tepat, tanpa detakan kedua', () => {
    // Kartu metrik antrean juga saringan: menekannya mengganti angkanya. Angkanya wajib
    // benar setelah itu, dan geraknya wajib tidak terulang — kalau berulang, mata pembaca
    // ditarik kembali ke skor pada setiap interaksi.
    const view = render(<Counter value={5} />)
    runToCompletion()

    view.rerender(<Counter value={41} />)

    expect(shown()).toBe(41)
  })

  test('angka nol tetap nol dan tidak memicu animasi apa pun', () => {
    render(<Counter value={0} />)
    runToCompletion()

    expect(shown()).toBe(0)
  })
})

describe('useCountUp menghormati prefers-reduced-motion', () => {
  test('langsung berada di nilai akhir pada bingkai pertama', () => {
    vi.stubGlobal(
      'matchMedia',
      vi.fn().mockImplementation((query: string) => ({
        matches: query.includes('prefers-reduced-motion'),
        media: query,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    )

    render(<Counter value={29} />)

    // Tanpa memajukan waktu sama sekali.
    expect(shown()).toBe(29)
    vi.unstubAllGlobals()
  })
})

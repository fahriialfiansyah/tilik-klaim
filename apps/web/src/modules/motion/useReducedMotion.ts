import { useSyncExternalStore } from 'react'

const QUERY = '(prefers-reduced-motion: reduce)'

function query(): MediaQueryList | null {
  // Dijaga: jsdom pada beberapa versi tidak memasang matchMedia sama sekali, dan
  // pengujian komponen tidak boleh gagal karena alasan itu.
  return typeof window === 'undefined' ? null : (window.matchMedia?.(QUERY) ?? null)
}

function subscribe(onChange: () => void): () => void {
  const list = query()
  if (!list) {
    return () => {}
  }
  list.addEventListener('change', onChange)
  return () => list.removeEventListener('change', onChange)
}

function getSnapshot(): boolean {
  return query()?.matches ?? false
}

/** Tanpa `window` tidak ada preferensi yang bisa dibaca; anggap gerak dimatikan. */
function getServerSnapshot(): boolean {
  return true
}

/**
 * Apakah pengguna meminta gerak dikurangi.
 *
 * Dipakai untuk gerak yang dijalankan JavaScript dan tidak bisa dijangkau sakelar
 * `@media (prefers-reduced-motion: reduce)` di `src/styles/motion.css` — misalnya
 * angka yang berdetak, yang harus langsung berada di nilai akhirnya.
 *
 * Berlangganan, bukan membaca sekali: pengguna bisa mengubah preferensi sistem
 * sementara aplikasi terbuka, dan bacaan sekali-pakai akan tetap bergerak sesudahnya.
 */
export function useReducedMotion(): boolean {
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot)
}

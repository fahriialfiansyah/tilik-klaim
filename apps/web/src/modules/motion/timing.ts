/**
 * Durasi gerak, dalam milidetik.
 *
 * Ini **cerminan** dari custom property di `src/styles/motion.css`, untuk animasi yang
 * dijalankan JavaScript dan tidak bisa membaca nilai CSS tanpa memaksa layout.
 * `timing.test.ts` membaca kedua berkas dan gagal kalau keduanya berbeda, sehingga
 * duplikasi ini tidak bisa diam-diam menyimpang.
 */
export const MOTION = {
  /** Perubahan keadaan di tempat — warna, batas, latar. */
  fast: 120,
  /** Permukaan kecil masuk/keluar — tooltip, menu, baris. */
  base: 180,
  /** Permukaan besar — dialog, laci. */
  surface: 240,
  /** Tata letak dan pengisian meter. Batas atas untuk alat yang dipakai seharian. */
  layout: 320,
  /** Angka besar berdetak ke nilainya. */
  count: 300,
  /** Jeda antar item dalam satu daftar bertahap. */
  stagger: 40,
} as const

/** Keluar cepat lalu melambat — benda yang datang terasa mendarat, bukan meluncur. */
export const EASE_OUT = [0.16, 1, 0.3, 1] as const

/** Detik, karena Motion mengukur durasi dalam detik sementara CSS memakai milidetik. */
const MS_PER_SECOND = 1000

export function seconds(ms: number): number {
  return ms / MS_PER_SECOND
}

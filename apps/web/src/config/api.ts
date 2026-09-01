/**
 * Alamat dasar API, satu-satunya tempat kode web mengetahuinya.
 *
 * Nilainya dibekukan saat build, bukan saat runtime — Rsbuild mengganti
 * `import.meta.env.PUBLIC_API_BASE_URL` dengan teks literal ketika bundel dibuat. Karena itu
 * mengubah variabel ini di Vercel menuntut *redeploy*, bukan sekadar restart.
 */

const DEFAULT_API_BASE_URL = 'http://localhost:8000'

const TRAILING_SLASH = /\/+$/

/**
 * Garis miring di ujung dibuang supaya `${API_BASE_URL}/v1/cases` tidak pernah menjadi
 * `//v1/cases`. Sebuah kotak isian di dasbor Vercel terlalu mudah diisi dengan garis miring
 * penutup untuk dijadikan asumsi diam-diam.
 */
export const API_BASE_URL: string = (
  import.meta.env.PUBLIC_API_BASE_URL ?? DEFAULT_API_BASE_URL
).replace(TRAILING_SLASH, '')

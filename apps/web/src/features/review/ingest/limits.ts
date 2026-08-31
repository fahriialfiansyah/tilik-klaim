/**
 * Submission limits, mirrored from `apps/backend/app/config.py`.
 *
 * `brief/01_INGEST_VALIDASI.md` § 2.1 requires the limits to be readable **before** an upload
 * rather than after a failure, and § 8 requires an oversized file to be refused in the
 * interface before it is sent. Both need the numbers here.
 *
 * The client check is a courtesy, never the enforcement: the server guards size and depth
 * *before* anything parses the payload, because a limit enforced after parsing is not a limit.
 * These constants existing here does not make the browser trustworthy — it makes it polite.
 *
 * **If `app/config.py` changes, change these.** Showing a limit that is not the limit is worse
 * than showing none: an operator trims a file to a number that was never real and it still
 * fails.
 */

const BYTES_PER_MIB = 1024 * 1024

/** `Settings.max_bundle_bytes` — 8 MiB. */
export const MAX_BUNDLE_BYTES = 8 * BYTES_PER_MIB

/** `Settings.max_json_depth`. */
export const MAX_JSON_DEPTH = 32

export const ACCEPTED_EXTENSIONS = ['.json'] as const
export const ACCEPT_ATTRIBUTE = 'application/json,.json'

export function formatBytes(bytes: number): string {
  const mib = bytes / BYTES_PER_MIB
  return mib >= 1 ? `${Math.round(mib)} MB` : `${Math.round(bytes / 1024)} kB`
}

export type FileRejection = {
  readonly code: 'TOO_LARGE' | 'WRONG_TYPE' | 'EMPTY'
  readonly message: string
}

/**
 * Refuse a file in the browser, naming the limit it broke.
 *
 * Returns `null` when the file is worth sending. The rejection carries the number, because
 * "file too large" without the limit leaves an operator guessing how much to cut.
 */
export function rejectFile(file: File): FileRejection | null {
  if (file.size === 0) {
    return { code: 'EMPTY', message: 'Berkas ini kosong — tidak ada isi untuk diperiksa.' }
  }
  if (file.size > MAX_BUNDLE_BYTES) {
    return {
      code: 'TOO_LARGE',
      message: `Berkas berukuran ${formatBytes(file.size)}, melampaui batas ${formatBytes(
        MAX_BUNDLE_BYTES,
      )}. Berkas tidak dikirim.`,
    }
  }
  const isJson =
    file.type === 'application/json' ||
    ACCEPTED_EXTENSIONS.some((extension) => file.name.toLowerCase().endsWith(extension))
  if (!isJson) {
    return {
      code: 'WRONG_TYPE',
      message: `Tipe berkas tidak diterima. Kirim satu berkas ${ACCEPTED_EXTENSIONS.join(' atau ')}.`,
    }
  }
  return null
}

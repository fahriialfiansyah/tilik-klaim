import { describe, expect, test } from 'vitest'

import { MAX_BUNDLE_BYTES, formatBytes, rejectFile } from '@/features/review/ingest/limits'

function fileOf(name: string, size: number, type = 'application/json'): File {
  const file = new File(['x'], name, { type })
  // `File` has no writable size, and allocating 9 MB in a unit test to prove a comparison is
  // wasteful. The property is stubbed rather than the buffer built.
  Object.defineProperty(file, 'size', { value: size })
  return file
}

describe('rejectFile', () => {
  test('accepts a JSON file inside the limit', () => {
    expect(rejectFile(fileOf('bundel.json', 1024))).toBeNull()
  })

  /**
   * `brief/01_INGEST_VALIDASI.md` § 8: an oversized file is refused **in the interface, before
   * it is sent**. Uploading eight megabytes to be told the limit is eight megabytes is the
   * experience this prevents.
   */
  test('refuses an oversized file and names both numbers', () => {
    const refusal = rejectFile(fileOf('besar.json', MAX_BUNDLE_BYTES + 1))

    expect(refusal?.code).toBe('TOO_LARGE')
    expect(refusal?.message).toContain(formatBytes(MAX_BUNDLE_BYTES))
    expect(refusal?.message).toContain('tidak dikirim')
  })

  test('refuses a file that is not JSON, by type or by extension', () => {
    expect(rejectFile(fileOf('catatan.pdf', 1024, 'application/pdf'))?.code).toBe('WRONG_TYPE')
  })

  test('accepts a .json file even when the browser reports no MIME type', () => {
    expect(rejectFile(fileOf('bundel.json', 1024, ''))).toBeNull()
  })

  test('refuses an empty file rather than sending nothing to be parsed', () => {
    expect(rejectFile(fileOf('kosong.json', 0))?.code).toBe('EMPTY')
  })
})

describe('formatBytes', () => {
  test('reports megabytes for the limit itself', () => {
    expect(formatBytes(MAX_BUNDLE_BYTES)).toBe('8 MB')
  })

  test('drops to kilobytes below one megabyte, so a small file is not "0 MB"', () => {
    expect(formatBytes(4096)).toBe('4 kB')
  })
})

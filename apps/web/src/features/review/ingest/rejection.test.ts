import { describe, expect, test } from 'vitest'

import { fromApiError, fromFileRejection, isBundleRejection } from '@/features/review/ingest/rejection'
import { ApiError, NetworkError } from '@/lib/http'

describe('telling a refused bundle from a broken service', () => {
  /**
   * The distinction an operator acts on. A refused bundle will be refused identically on every
   * retry, so offering "coba lagi" for one is wrong advice; a service outage will not be fixed
   * by editing the file.
   */
  test('a BUNDLE_* code is the bundle being refused', () => {
    expect(
      isBundleRejection(
        new ApiError(400, { code: 'BUNDLE_MALFORMED_JSON', detail: 'not json' }),
      ),
    ).toBe(true)
  })

  test('any other API error is a service failure', () => {
    expect(
      isBundleRejection(new ApiError(500, { code: 'UNEXPECTED', detail: 'boom' })),
    ).toBe(false)
  })

  test('a network error is a service failure', () => {
    expect(isBundleRejection(new NetworkError(new Error('offline')))).toBe(false)
  })
})

describe('fromApiError', () => {
  test('keeps the resources the server named', () => {
    const rejection = fromApiError(
      new ApiError(422, {
        code: 'BUNDLE_DANGLING_REFERENCE',
        detail: 'Procedure/PROC-9 is referenced but not present',
        issues: [
          {
            code: 'BUNDLE_DANGLING_REFERENCE',
            resource_type: 'Procedure',
            resource_id: 'PROC-9',
            detail: 'Procedure/PROC-9 is referenced but not present',
          },
        ],
      }),
    )

    expect(rejection.issues).toHaveLength(1)
    expect(rejection.issues[0].resource_id).toBe('PROC-9')
    expect(rejection.source).toBe('server')
  })

  /**
   * A truncated file has no resource to point at, so the envelope carries no issues. Rendering
   * an empty error table there would say "nothing was wrong" about a rejected file.
   */
  test('synthesises one issue when the server named no resource', () => {
    const rejection = fromApiError(
      new ApiError(400, { code: 'BUNDLE_MALFORMED_JSON', detail: 'Expecting value: line 1' }),
    )

    expect(rejection.issues).toHaveLength(1)
    expect(rejection.issues[0].code).toBe('BUNDLE_MALFORMED_JSON')
    expect(rejection.issues[0].resource_id).toBeNull()
    expect(rejection.issues[0].detail).toContain('Expecting value')
  })

  test('translates the code into working language rather than echoing the server', () => {
    const rejection = fromApiError(
      new ApiError(413, { code: 'BUNDLE_TOO_LARGE', detail: 'payload too large' }),
    )
    expect(rejection.message).toMatch(/batas ukuran/)
  })
})

describe('fromFileRejection', () => {
  test('marks a browser refusal as client-side, with no issues to list', () => {
    const rejection = fromFileRejection({ code: 'TOO_LARGE', message: 'Berkas 9 MB.' })

    expect(rejection.source).toBe('client')
    expect(rejection.issues).toHaveLength(0)
    expect(rejection.message).toBe('Berkas 9 MB.')
  })
})

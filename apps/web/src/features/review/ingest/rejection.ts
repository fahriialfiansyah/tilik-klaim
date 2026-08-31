import { issueExplanation } from '@/features/review/ingest/labels'
import type { FileRejection } from '@/features/review/ingest/limits'
import type { ValidationIssue } from '@/features/review/ingest/types'
import { ApiError } from '@/lib/http'

/**
 * A bundle the system will not screen, from whichever of the three places said so.
 *
 * The distinction that matters to an operator is **"my file is wrong" versus "the service is
 * down"**, and the API does not draw it along one axis:
 *
 * * the **browser** refuses a file that breaks a stated limit, before anything is sent;
 * * the **server** refuses one *before parsing* — too large, wrong content type, too deep,
 *   malformed JSON — with a `4xx` error envelope;
 * * the **server** accepts one and reports `status: INVALID` with issues, at `200`.
 *
 * All three mean the same thing on screen: not screenable, here is why, fix it and resubmit.
 * Rendering the middle case as a service failure — which is what a plain `catch` produces —
 * would tell an operator to retry a file that will be refused identically every time.
 */
export type BundleRejection = {
  /** `TOO_LARGE`, `WRONG_TYPE`, `EMPTY`, or a stable `BUNDLE_*` code from the API. */
  readonly code: string
  readonly message: string
  readonly issues: readonly ValidationIssue[]
  readonly source: 'client' | 'server'
}

/** Codes the API uses for a bundle it refuses. Anything else is a genuine service failure. */
const BUNDLE_REJECTION_PREFIX = 'BUNDLE_'

export function isBundleRejection(cause: unknown): cause is ApiError {
  return cause instanceof ApiError && cause.code.startsWith(BUNDLE_REJECTION_PREFIX)
}

export function fromApiError(error: ApiError): BundleRejection {
  return {
    code: error.code,
    message: issueExplanation(error.code),
    // The envelope carries per-resource issues for some codes and none for others — a truncated
    // file has no resource to point at. The code itself is then the whole finding.
    issues:
      error.issues.length > 0
        ? error.issues
        : [
            {
              code: error.code,
              resource_type: null,
              resource_id: null,
              detail: error.message,
            },
          ],
    source: 'server',
  }
}

export function fromFileRejection(refusal: FileRejection): BundleRejection {
  return {
    code: refusal.code,
    message: refusal.message,
    issues: [],
    source: 'client',
  }
}

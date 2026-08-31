import type {
  IngestBundleResponse,
  SamplePayload,
  SampleSummary,
  ScreenResponse,
} from '@/features/review/ingest/types'
import { NetworkError, request } from '@/lib/http'

/**
 * Submit one bundle for validation.
 *
 * The body is sent as the raw JSON text the caller already holds rather than re-serialised from
 * a parsed object. Round-tripping through `JSON.parse`/`stringify` would change key order and
 * whitespace, and the response's `input_hash` is computed over the payload — a hash that
 * differs from the one an operator would get by hashing their own file is a reproducibility
 * claim the system cannot keep.
 */
export async function ingestBundle(payload: string): Promise<IngestBundleResponse> {
  return request<IngestBundleResponse>('/bundles', { method: 'POST', body: payload })
}

/**
 * Screen a validated bundle.
 *
 * The request body is empty by design — `ScreenRequest` carries no detector, threshold, or mode
 * selection. `sprint/00-app-spec.md` § 5 forbids a configuration wizard on this screen, and the
 * absence of options in the contract is what makes that enforceable rather than a UI promise.
 */
export async function screenBundle(ingestionId: string): Promise<ScreenResponse> {
  return request<ScreenResponse>(`/bundles/${encodeURIComponent(ingestionId)}/screen`, {
    method: 'POST',
    body: '{}',
  })
}

/**
 * The five curated demo scenarios, served as static files from the app's own origin.
 *
 * They are generated from the backend's gold fixtures by
 * `apps/backend/scripts/export_demo_samples.py`, with the fixtures' expected outcomes stripped;
 * `tests/test_demo_samples.py` fails if they drift. Static because
 * `docs/canonical/08_demo_runbook.md` requires the demo to run with no external network, and
 * same-origin because everything else on this app is.
 */
export async function fetchSampleIndex(): Promise<readonly SampleSummary[]> {
  return fetchJson<readonly SampleSummary[]>('/samples/index.json')
}

export async function fetchSample(scenario: string): Promise<SamplePayload> {
  return fetchJson<SamplePayload>(`/samples/${encodeURIComponent(scenario)}.json`)
}

/** Static assets do not go through `/v1`, so they do not go through `request`. */
async function fetchJson<T>(path: string): Promise<T> {
  let response: Response
  try {
    response = await fetch(path)
  } catch (cause) {
    throw new NetworkError(cause)
  }
  if (!response.ok) {
    throw new Error(`Berkas contoh tidak dapat dimuat (${response.status}).`)
  }
  return (await response.json()) as T
}

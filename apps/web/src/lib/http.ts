/** The API's error envelope. Every failure arrives in this shape. */
export type ApiErrorBody = {
  readonly code: string
  readonly detail: string
  readonly issues?: readonly unknown[]
}

/** A failed request, carrying the server's own code and message rather than a generic string. */
export class ApiError extends Error {
  readonly code: string
  readonly status: number

  constructor(status: number, body: ApiErrorBody) {
    super(body.detail)
    this.name = 'ApiError'
    this.code = body.code
    this.status = status
  }
}

/** Raised when the request never reached the service at all. */
export class NetworkError extends Error {
  constructor(cause: unknown) {
    super('Layanan tidak merespons.')
    this.name = 'NetworkError'
    this.cause = cause
  }
}

const BASE = '/v1'

/**
 * Same-origin JSON request. Paths are relative, so the Rsbuild dev proxy handles them in
 * development and a reverse proxy handles them in production — no origin is baked into the bundle.
 *
 * Errors are never swallowed: a non-2xx becomes an `ApiError` carrying the server's own code, and
 * an unreachable service becomes a `NetworkError`. Callers must be able to tell "no cases" from
 * "the service is down", because those are different screens with different next actions.
 */
export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${BASE}${path}`, {
      ...init,
      headers: { 'content-type': 'application/json', ...init?.headers },
    })
  } catch (cause) {
    throw new NetworkError(cause)
  }

  if (!response.ok) {
    let body: ApiErrorBody = { code: 'UNEXPECTED', detail: response.statusText }
    try {
      body = (await response.json()) as ApiErrorBody
    } catch {
      // A non-JSON error body (a proxy 502, say) still has a status worth reporting.
    }
    throw new ApiError(response.status, body)
  }

  return (await response.json()) as T
}

/** Builds a query string, dropping keys the caller left unset. */
export function query(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== '') {
      search.set(key, String(value))
    }
  }
  const encoded = search.toString()
  return encoded ? `?${encoded}` : ''
}

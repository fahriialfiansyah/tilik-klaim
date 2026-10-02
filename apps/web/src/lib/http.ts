import i18n from '@/modules/i18n/config'
import { DEFAULT_LOCALE } from '@/modules/i18n/locales'
import { currentUser } from '@/features/auth/useSession'

/**
 * One problem the server found, pointed at a specific resource.
 *
 * Mirrors `apps/backend/app/errors.py::ValidationIssue`. It travels on the error envelope as
 * well as on a 200 ingest response, because a bundle can be refused *before* parsing (too
 * large, malformed, too deep) or *after* it (a dangling reference) — and an operator needs the
 * same actionable detail either way.
 */
export type ApiIssue = {
  readonly code: string
  readonly resource_type: string | null
  readonly resource_id: string | null
  readonly detail: string
}

/** The API's error envelope. Every failure arrives in this shape. */
export type ApiErrorBody = {
  readonly code: string
  readonly detail: string
  readonly issues?: readonly ApiIssue[]
}

/** A failed request, carrying the server's own code and message rather than a generic string. */
export class ApiError extends Error {
  readonly code: string
  readonly status: number
  /**
   * The resources the server named, when it named any.
   *
   * Dropping these was a real loss on the ingest screen: a malformed or oversized bundle is
   * refused with a 4xx envelope rather than a 200 report, and without the issues the screen
   * could only say "the request failed" about a file whose exact problem the server had already
   * identified.
   */
  readonly issues: readonly ApiIssue[]

  constructor(status: number, body: ApiErrorBody) {
    super(body.detail)
    this.name = 'ApiError'
    this.code = body.code
    this.status = status
    this.issues = body.issues ?? []
  }
}

/** Raised when the request never reached the service at all. */
export class NetworkError extends Error {
  constructor(cause: unknown) {
    super(i18n.t('common:state.serviceDown'))
    this.name = 'NetworkError'
    this.cause = cause
  }
}

const BASE = '/v1'

/**
 * The two headers every request carries, taken from the signed-in persona.
 *
 * **Both are forgeable, and that is documented rather than hidden** — ADR-0006 § 4. Anyone with
 * `curl` can send any role; what the server does is refuse what the *claimed* role may not do
 * and record the claim on every audit event. Verifying the claim is a production requirement
 * this prototype states and does not meet.
 *
 * The role header replaces a hardcoded `ACTOR_ROLE = 'reviewer'` that used to live in one
 * feature's api module and travel on every call regardless of who was looking at the screen.
 */
function actorHeaders(): Record<string, string> {
  const user = currentUser()
  if (!user) {
    return {}
  }
  return { 'X-Actor-Role': user.role, 'X-Actor-Id': user.user_id }
}

/**
 * The language this request wants its catalog text in.
 *
 * Sent on every call rather than only on the ones that obviously carry prose: the reason
 * sentence, the counter-evidence, the band explanation and the timeline labels all come from
 * the server, and an endpoint that grows a sentence later would otherwise answer in the wrong
 * language until somebody noticed. The server falls back to the working language for anything
 * it cannot honour, so sending it is never worse than omitting it.
 */
function languageHeader(): Record<string, string> {
  return { 'Accept-Language': i18n.language || DEFAULT_LOCALE }
}

/**
 * The persona and language headers, for callers that cannot go through `request` — a streamed
 * body has to be read with `fetch` directly, and must still say who is asking and in which
 * language, or the server answers a role and a locale nobody chose.
 */
export function requestHeaders(): Record<string, string> {
  return { ...actorHeaders(), ...languageHeader() }
}

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
      headers: {
        'content-type': 'application/json',
        ...actorHeaders(),
        ...languageHeader(),
        ...init?.headers,
      },
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

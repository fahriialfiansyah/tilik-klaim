import type {
  AssistantAnswer,
  AssistantEvent,
  AssistantQuestion,
} from '@/features/review/assistant/types'
import { ApiError, NetworkError, request, requestHeaders, type ApiErrorBody } from '@/lib/http'
import { readSseStream } from '@/lib/sse'

const ENDPOINT = '/v1/assistant/answers'
const EVENT_NAMES: ReadonlySet<string> = new Set(['status', 'tool', 'done', 'error'])

/**
 * Ask, and stream the reading that leads to the answer.
 *
 * `fetch` with a streaming body rather than `EventSource`, for the same reasons as the briefing,
 * plus one of its own: this is a POST, and `EventSource` cannot send one. Resolves when the server
 * closes the stream; rejects on transport failure so the caller can ask once more, unstreamed.
 */
export async function streamAnswer(
  body: AssistantQuestion,
  onEvent: (event: AssistantEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  let response: Response
  try {
    response = await fetch(ENDPOINT, {
      method: 'POST',
      headers: {
        accept: 'text/event-stream',
        'content-type': 'application/json',
        ...requestHeaders(),
      },
      body: JSON.stringify(body),
      signal,
    })
  } catch (cause) {
    if (signal?.aborted) {
      throw cause
    }
    throw new NetworkError(cause)
  }
  if (!response.ok) {
    // A refusal arrives as the ordinary error envelope, not as events. Carry its code, so the
    // caller can tell "you may not" from "the stream broke" and not retry the first.
    let envelope: ApiErrorBody = { code: 'UNEXPECTED', detail: response.statusText }
    try {
      envelope = (await response.json()) as ApiErrorBody
    } catch {
      // A proxy's HTML error page still has a status worth reporting.
    }
    throw new ApiError(response.status, envelope)
  }
  if (!response.body) {
    throw new NetworkError(new Error('assistant stream had no body'))
  }
  await readSseStream(response.body, EVENT_NAMES, (frame) => onEvent(frame as AssistantEvent))
}

/** The same answer in one response — the fallback when a proxy will not stream. */
export async function fetchAnswer(
  body: AssistantQuestion,
  signal?: AbortSignal,
): Promise<AssistantAnswer> {
  return request<AssistantAnswer>('/assistant/answers?stream=false', {
    method: 'POST',
    body: JSON.stringify(body),
    signal,
  })
}

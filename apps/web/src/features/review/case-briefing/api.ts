import { parseSseChunk } from '@/features/review/case-briefing/events'
import type { BriefingEvent, CaseBriefing } from '@/features/review/case-briefing/types'
import { NetworkError, request } from '@/lib/http'

const BASE = '/v1'

/**
 * Stream the briefing as Server-Sent Events.
 *
 * `fetch` with a streaming body rather than `EventSource`: it honours the same relative `/v1`
 * base and proxy as every other call, it can be aborted, and its frames go through the same pure
 * parser the tests exercise. Resolves when the server closes the stream; rejects on transport
 * failure so the caller can fall back to the one-shot answer.
 */
export async function streamBriefing(
  caseId: string,
  onEvent: (event: BriefingEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  let response: Response
  try {
    response = await fetch(`${BASE}/cases/${encodeURIComponent(caseId)}/briefing`, {
      headers: { accept: 'text/event-stream' },
      signal,
    })
  } catch (cause) {
    throw new NetworkError(cause)
  }
  if (!response.ok || !response.body) {
    throw new NetworkError(new Error(`briefing stream answered ${response.status}`))
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  for (;;) {
    const { value, done } = await reader.read()
    if (done) {
      break
    }
    buffer += decoder.decode(value, { stream: true })
    const parsed = parseSseChunk(buffer)
    buffer = parsed.rest
    parsed.events.forEach(onEvent)
  }
}

/** The same briefing in one response — the fallback when a proxy will not stream. */
export async function fetchBriefing(caseId: string): Promise<CaseBriefing> {
  return request<CaseBriefing>(`/cases/${encodeURIComponent(caseId)}/briefing?stream=false`)
}

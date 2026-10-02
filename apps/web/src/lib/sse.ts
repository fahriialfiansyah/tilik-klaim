/**
 * A Server-Sent Events frame parser, shared by every streamed endpoint.
 *
 * Pure: a buffer in, complete events and the unfinished remainder out. The briefing and the
 * assistant stream the same frame shape (`event: x\ndata: {...}\n\n`) and differ only in which
 * event names they accept, so the names are the one parameter.
 */

export type SseFrame = { readonly name: string; readonly data: unknown }

/**
 * Split a text buffer into complete frames. Whatever follows the last blank line is returned as
 * `rest` for the next chunk to complete. Frames with an unknown name, no data, or data the server
 * had not finished writing are dropped rather than guessed at.
 */
export function parseSseFrames(
  buffer: string,
  names: ReadonlySet<string>,
): { readonly frames: readonly SseFrame[]; readonly rest: string } {
  // Servers and proxies may end lines with CRLF; the frame grammar is the same either way.
  const chunks = buffer.replace(/\r\n?/g, '\n').split('\n\n')
  const rest = chunks.pop() ?? ''
  const frames: SseFrame[] = []
  for (const chunk of chunks) {
    const frame = parseFrame(chunk, names)
    if (frame) {
      frames.push(frame)
    }
  }
  return { frames, rest }
}

function parseFrame(chunk: string, names: ReadonlySet<string>): SseFrame | null {
  let name: string | null = null
  const dataLines: string[] = []
  for (const line of chunk.split('\n')) {
    if (line.startsWith('event: ')) {
      name = line.slice('event: '.length).trim()
    } else if (line.startsWith('data: ')) {
      dataLines.push(line.slice('data: '.length))
    }
  }
  if (!name || !names.has(name) || dataLines.length === 0) {
    return null
  }
  try {
    return { name, data: JSON.parse(dataLines.join('\n')) }
  } catch {
    // A frame the server did not finish writing is not an event; the next chunk completes it.
    return null
  }
}

/**
 * Read a streamed response body to its end, handing each complete frame to `onFrame`.
 *
 * Resolves when the server closes the stream. A transport failure rejects, so the caller can
 * fall back to its one-shot variant.
 */
export async function readSseStream(
  body: ReadableStream<Uint8Array>,
  names: ReadonlySet<string>,
  onFrame: (frame: SseFrame) => void,
): Promise<void> {
  const reader = body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  for (;;) {
    const { value, done } = await reader.read()
    if (done) {
      // A last frame the server ended without a trailing blank line is still a frame.
      const tail = parseSseFrames(`${buffer}${decoder.decode()}\n\n`, names)
      tail.frames.forEach(onFrame)
      return
    }
    buffer += decoder.decode(value, { stream: true })
    const parsed = parseSseFrames(buffer, names)
    buffer = parsed.rest
    parsed.frames.forEach(onFrame)
  }
}

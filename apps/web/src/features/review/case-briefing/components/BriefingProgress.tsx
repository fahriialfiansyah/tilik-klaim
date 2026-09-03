import { Loader2 } from 'lucide-react'

import { PHASE_LABELS, toolLabel } from '@/features/review/case-briefing/labels'
import type { BriefingState } from '@/features/review/case-briefing/events'

/**
 * What the briefing read, in order. This log is the transparency artifact: the answer to "what
 * did it actually look at", which an opaque summary cannot give. Announced politely so a screen
 * reader hears progress without losing its place.
 */
export function BriefingProgress({ state }: { readonly state: BriefingState }) {
  const isStreaming = state.status === 'streaming'
  return (
    <div role="status" aria-live="polite" className="rounded-md border border-line bg-sunk px-[13px] py-[10px]">
      <p className="flex items-center gap-2 text-meta text-ink-2">
        {isStreaming ? <Loader2 aria-hidden className="size-3 animate-spin" /> : null}
        {state.phase ? PHASE_LABELS[state.phase] : 'Menunggu'}
        {state.phaseDetail && state.phase !== 'DONE' ? (
          <span className="text-ink-3">· {toolLabel(state.phaseDetail)}</span>
        ) : null}
      </p>
      {state.toolCalls.length > 0 ? (
        <ol className="mt-2 space-y-[3px]">
          {state.toolCalls.map((call, index) => (
            <li key={`${call.tool}-${index}`} className="flex flex-wrap gap-x-2 text-meta">
              <span data-numeric className="font-mono text-ink-3">
                {index + 1}.
              </span>
              <span>{toolLabel(call.tool)}</span>
              {Object.entries(call.arguments).map(([key, value]) => (
                <span key={key} data-numeric className="font-mono text-ink-3">
                  {key}={value}
                </span>
              ))}
            </li>
          ))}
        </ol>
      ) : null}
    </div>
  )
}

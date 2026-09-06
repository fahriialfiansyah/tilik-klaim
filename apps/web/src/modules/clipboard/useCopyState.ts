import { useCallback, useState } from 'react'

import { copyText } from '@/lib/clipboard'

/** Long enough to be read, short enough that the button returns to its resting label. */
const SETTLE_MS = 1600

/** Resting, confirmed, or refused — a copy button has three states, not two. */
export type CopyState = 'idle' | 'copied' | 'failed'

/**
 * Drive a copy button that tells the truth about whether the copy happened.
 *
 * The third state is the point. `navigator.clipboard` is absent outside a secure context, which
 * is exactly how this app is demonstrated — over plain HTTP on a LAN address — and a button
 * that reports success there sends an operator away believing they hold a hash they do not.
 */
export function useCopyState(): readonly [CopyState, (text: string) => Promise<void>] {
  const [state, setState] = useState<CopyState>('idle')

  const copy = useCallback(async (text: string) => {
    setState((await copyText(text)) ? 'copied' : 'failed')
    window.setTimeout(() => setState('idle'), SETTLE_MS)
  }, [])

  return [state, copy]
}

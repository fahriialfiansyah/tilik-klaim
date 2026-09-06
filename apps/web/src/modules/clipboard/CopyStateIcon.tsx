import { Check, Copy, X } from 'lucide-react'

import type { CopyState } from '@/modules/clipboard/useCopyState'

/** The icon half of a copy button, so the three states are drawn the same way everywhere. */
export function CopyStateIcon({ state }: { readonly state: CopyState }) {
  if (state === 'copied') {
    return <Check aria-hidden />
  }
  if (state === 'failed') {
    return <X aria-hidden />
  }
  return <Copy aria-hidden />
}

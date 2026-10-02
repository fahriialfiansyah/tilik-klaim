import { create } from 'zustand'

import { newTurn, type Turn } from '@/features/review/assistant/conversation'
import type { AssistantScope } from '@/features/review/assistant/types'
import { useSession } from '@/features/auth/useSession'

/**
 * The conversation, in this tab's memory and nowhere else.
 *
 * Deliberately **not persisted**: ADR-0007 § 3 says the conversation is gone on reload, and a
 * conversation kept in `localStorage` would outlive the session that asked it — the next persona
 * at the same machine would open the page onto the last one's questions. It survives moving
 * between pages, so a reviewer can open a cited case and come back to where they were.
 *
 * It is cleared whenever the signed-in persona changes, for the same reason.
 */
type AssistantStore = {
  readonly turns: readonly Turn[]
  /** Add a streaming turn and return its id. */
  readonly start: (question: string, scope: AssistantScope) => string
  /** Replace one turn with `update(turn)`. A turn that no longer exists is left alone. */
  readonly update: (id: string, update: (turn: Turn) => Turn) => void
  readonly reset: () => void
}

let counter = 0

function nextId(): string {
  counter += 1
  return `turn-${Date.now().toString(36)}-${counter}`
}

export const useAssistantStore = create<AssistantStore>((set) => ({
  turns: [],
  start: (question, scope) => {
    const id = nextId()
    set((state) => ({ turns: [...state.turns, newTurn(id, question, scope)] }))
    return id
  },
  update: (id, update) =>
    set((state) => ({
      turns: state.turns.map((turn) => (turn.id === id ? update(turn) : turn)),
    })),
  reset: () => set({ turns: [] }),
}))

useSession.subscribe((state, previous) => {
  if (state.user?.user_id !== previous.user?.user_id) {
    useAssistantStore.getState().reset()
  }
})

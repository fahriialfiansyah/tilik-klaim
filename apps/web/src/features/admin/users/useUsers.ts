import { useCallback, useEffect, useState } from 'react'

import { fetchUserAudit, fetchUsers, updateUser } from '@/features/admin/users/api'
import type { UserAuditEvent } from '@/features/admin/users/types'
import { ROLE_LABEL } from '@/features/auth/labels'
import { isRole, type Role, type StaffUser } from '@/features/auth/types'
import { ApiError } from '@/lib/http'

/**
 * The roster and its history, loaded together and reloaded together.
 *
 * Four states, as `design/DESIGN.md` requires: `loading`, `ready`, `empty` (a roster with no
 * rows — which should never happen with a seeded database, and is therefore worth showing
 * plainly rather than as a blank table), and `failed`.
 *
 * A refused change is *not* a page-level failure: the table keeps its data and the refusal is
 * reported above it as an alert, because "you may not deactivate yourself" is an answer to one
 * action, not an outage.
 */
export type RosterStatus = 'loading' | 'ready' | 'empty' | 'failed'

export type Refusal = { readonly code: string; readonly message: string }

export type UserPatch = { readonly role?: Role; readonly is_active?: boolean }

/**
 * The change just made, and the change that would put it back.
 *
 * **Undo appends; it does not erase.** Applying `patch` writes a *new* event recording the move
 * back, and the original stays in the trail exactly as it was — the same guarantee ADR-0001
 * gives a case disposition, where a correction supersedes rather than overwrites. An "undo" that
 * deleted the event it reversed would be the one control on this page capable of rewriting the
 * history the page exists to keep.
 */
export type UndoableChange = {
  readonly userId: string
  readonly patch: UserPatch
  readonly summary: string
}

type Roster = {
  readonly status: RosterStatus
  readonly users: readonly StaffUser[]
  readonly events: readonly UserAuditEvent[]
  readonly error: Error | null
  readonly pendingUserId: string | null
  readonly refusal: Refusal | null
  readonly undoable: UndoableChange | null
  readonly reload: () => void
  readonly change: (userId: string, patch: UserPatch) => Promise<void>
  readonly undo: () => Promise<void>
  readonly dismissUndo: () => void
}

export function useUsers(): Roster {
  const [status, setStatus] = useState<RosterStatus>('loading')
  const [users, setUsers] = useState<readonly StaffUser[]>([])
  const [events, setEvents] = useState<readonly UserAuditEvent[]>([])
  const [error, setError] = useState<Error | null>(null)
  const [pendingUserId, setPendingUserId] = useState<string | null>(null)
  const [refusal, setRefusal] = useState<Refusal | null>(null)
  const [undoable, setUndoable] = useState<UndoableChange | null>(null)
  const [reloadToken, setReloadToken] = useState(0)

  const reload = useCallback(() => setReloadToken((token) => token + 1), [])

  useEffect(() => {
    let active = true
    setStatus('loading')
    setError(null)

    Promise.all([fetchUsers(), fetchUserAudit()])
      .then(([roster, audit]) => {
        if (!active) {
          return
        }
        setUsers(roster.users)
        setEvents(audit.events)
        setStatus(roster.users.length === 0 ? 'empty' : 'ready')
      })
      .catch((cause: unknown) => {
        if (!active) {
          return
        }
        setUsers([])
        setEvents([])
        setError(cause instanceof Error ? cause : new Error(String(cause)))
        setStatus('failed')
      })

    return () => {
      active = false
    }
  }, [reloadToken])

  const apply = useCallback(
    async (userId: string, patch: UserPatch, { offerUndo }: { offerUndo: boolean }) => {
      setPendingUserId(userId)
      setRefusal(null)
      setUndoable(null)
      try {
        const outcome = await updateUser(userId, patch)
        // The server's row replaces the local one rather than being merged into it: it carries
        // the `updated_at` this change produced, and merging would leave two half-truths.
        setUsers((current) =>
          current.map((user) => (user.user_id === userId ? outcome.user : user)),
        )
        setEvents((current) => [...outcome.events, ...current])
        if (offerUndo) {
          setUndoable(describeUndo(outcome.user, outcome.events))
        }
      } catch (cause: unknown) {
        setRefusal(describeRefusal(cause))
      } finally {
        setPendingUserId(null)
      }
    },
    [],
  )

  const change = useCallback(
    (userId: string, patch: UserPatch) => apply(userId, patch, { offerUndo: true }),
    [apply],
  )

  // An undo offers no undo of its own. One step back is an escape from a mis-click; a pair of
  // buttons that flip each other forever is a control nobody can tell the state of.
  const undo = useCallback(async () => {
    if (undoable) {
      await apply(undoable.userId, undoable.patch, { offerUndo: false })
    }
  }, [apply, undoable])

  const dismissUndo = useCallback(() => setUndoable(null), [])

  return {
    status,
    users,
    events,
    error,
    pendingUserId,
    refusal,
    undoable,
    reload,
    change,
    undo,
    dismissUndo,
  }
}

/**
 * The way back, read off the events the server just wrote.
 *
 * Built from `value_before` rather than from the local row we held a moment ago: the events are
 * what was actually recorded, and a client-side "what it used to be" can disagree with them
 * after a concurrent change by a second administrator.
 */
function describeUndo(
  user: StaffUser,
  events: readonly UserAuditEvent[],
): UndoableChange | null {
  let patch: UserPatch = {}
  const said: string[] = []

  for (const event of events) {
    if (event.field === 'role' && event.value_before && isRole(event.value_before)) {
      patch = { ...patch, role: event.value_before }
      said.push(`peran menjadi ${ROLE_LABEL[user.role]}`)
    }
    if (event.field === 'is_active' && event.value_before !== null) {
      patch = { ...patch, is_active: event.value_before === 'true' }
      said.push(user.is_active ? 'akun diaktifkan kembali' : 'akun dinonaktifkan')
    }
  }

  if (said.length === 0) {
    return null
  }
  return {
    userId: user.user_id,
    patch,
    summary: `${user.full_name}: ${said.join(', ')}.`,
  }
}

function describeRefusal(cause: unknown): Refusal {
  if (cause instanceof ApiError) {
    return { code: cause.code, message: cause.message }
  }
  return {
    code: 'UNEXPECTED',
    message:
      cause instanceof Error
        ? `Perubahan tidak tersimpan: ${cause.message}`
        : 'Perubahan tidak tersimpan.',
  }
}

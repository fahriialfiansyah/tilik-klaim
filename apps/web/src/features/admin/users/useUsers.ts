import { useCallback, useEffect, useState } from 'react'

import { fetchUserAudit, fetchUsers, updateUser } from '@/features/admin/users/api'
import type { UserAuditEvent } from '@/features/admin/users/types'
import type { Role, StaffUser } from '@/features/auth/types'
import { ApiError } from '@/lib/http'

/**
 * The roster and its history, loaded together and reloaded together.
 *
 * Four states, as `design/DESIGN.md` requires: `loading`, `ready`, `empty` (a roster with no
 * rows — which should never happen with a seeded database, and is therefore worth showing
 * plainly rather than as a blank table), and `failed`.
 *
 * A refused change is *not* a page-level failure: the table keeps its data and the refusal is
 * reported beside the row it belongs to, because "you may not deactivate yourself" is an answer
 * to one action, not an outage.
 */
export type RosterStatus = 'loading' | 'ready' | 'empty' | 'failed'

export type Refusal = { readonly code: string; readonly message: string }

type Roster = {
  readonly status: RosterStatus
  readonly users: readonly StaffUser[]
  readonly events: readonly UserAuditEvent[]
  readonly error: Error | null
  readonly pendingUserId: string | null
  readonly refusal: Refusal | null
  readonly reload: () => void
  readonly change: (
    userId: string,
    patch: { readonly role?: Role; readonly is_active?: boolean },
  ) => Promise<void>
}

export function useUsers(): Roster {
  const [status, setStatus] = useState<RosterStatus>('loading')
  const [users, setUsers] = useState<readonly StaffUser[]>([])
  const [events, setEvents] = useState<readonly UserAuditEvent[]>([])
  const [error, setError] = useState<Error | null>(null)
  const [pendingUserId, setPendingUserId] = useState<string | null>(null)
  const [refusal, setRefusal] = useState<Refusal | null>(null)
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

  const change = useCallback(
    async (userId: string, patch: { readonly role?: Role; readonly is_active?: boolean }) => {
      setPendingUserId(userId)
      setRefusal(null)
      try {
        const outcome = await updateUser(userId, patch)
        // The server's row replaces the local one rather than being merged into it: it carries
        // the `updated_at` this change produced, and merging would leave two half-truths.
        setUsers((current) =>
          current.map((user) => (user.user_id === userId ? outcome.user : user)),
        )
        setEvents((current) => [...outcome.events, ...current])
      } catch (cause: unknown) {
        setRefusal(describeRefusal(cause))
      } finally {
        setPendingUserId(null)
      }
    },
    [],
  )

  return { status, users, events, error, pendingUserId, refusal, reload, change }
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

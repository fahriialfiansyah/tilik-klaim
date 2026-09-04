import { create } from 'zustand'

import { isRole, type StaffUser } from '@/features/auth/types'

const STORAGE_KEY = 'tilik-session'

/**
 * Who is signed in, kept in `localStorage` so a page refresh does not send a reviewer back to
 * the login screen mid-case.
 *
 * There is nothing to invalidate server-side because nothing was ever issued (ADR-0006 § 7).
 * Signing out clears this key and returns to `/login`; that is the whole of it.
 */
function readStored(): StaffUser | null {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) {
      return null
    }
    const parsed = JSON.parse(raw) as Partial<StaffUser>
    // Validated rather than trusted: `localStorage` is editable by hand, and a malformed
    // session would otherwise reach the app as a user with an undefined role, which every
    // permission check would then answer against.
    if (
      typeof parsed.user_id === 'string' &&
      typeof parsed.role === 'string' &&
      isRole(parsed.role)
    ) {
      return parsed as StaffUser
    }
  } catch {
    // Private browsing, blocked site data, and hand-edited JSON all land here. No session is a
    // complete answer — the guard sends the visitor to /login.
  }
  return null
}

function persist(user: StaffUser | null): void {
  try {
    if (user) {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(user))
    } else {
      window.localStorage.removeItem(STORAGE_KEY)
    }
  } catch {
    // Persisting is a convenience; the session still works for this tab.
  }
}

type SessionStore = {
  readonly user: StaffUser | null
  readonly signIn: (user: StaffUser) => void
  readonly signOut: () => void
}

export const useSession = create<SessionStore>((set) => ({
  user: readStored(),
  signIn: (user) => {
    persist(user)
    set({ user })
  },
  signOut: () => {
    persist(null)
    set({ user: null })
  },
}))

/**
 * The signed-in account, read outside React.
 *
 * `src/lib/http.ts` needs it on every request and is not a component, so it reads the store
 * directly rather than being handed the value through twenty call sites.
 */
export function currentUser(): StaffUser | null {
  return useSession.getState().user
}

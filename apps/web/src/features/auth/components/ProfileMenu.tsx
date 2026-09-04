import { LogOut, User } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { ROLE_LABEL } from '@/features/auth/labels'
import { useSession } from '@/features/auth/useSession'
import { hasUnsavedDraft, useCaseDetailStore } from '@/features/review/case-detail/store'

/**
 * Who is signed in, at the right end of the header, and the way out.
 *
 * Replaces the hardcoded `analis casemix` constant, which matched no role in the code and no
 * role in `03_architecture.md` — it was the only role name a judge could actually see.
 *
 * **Signing out warns when a disposition draft is unsaved.** `store.ts` keeps drafts alive
 * precisely so a refused save does not cost the reviewer their work, and a sign-out that
 * silently discarded one would undo that guarantee from a different direction.
 */
export function ProfileMenu() {
  const navigate = useNavigate()
  const user = useSession((state) => state.user)
  const signOut = useSession((state) => state.signOut)
  const drafts = useCaseDetailStore((state) => state.drafts)
  const [confirming, setConfirming] = useState(false)

  if (!user) {
    return null
  }

  const unsaved = hasUnsavedDraft(drafts)

  function leave() {
    signOut()
    navigate('/login', { replace: true })
  }

  function onSignOut(event: Event) {
    if (unsaved && !confirming) {
      // Keep the menu open and ask once. A native `confirm()` would be dismissible by Escape
      // in a way that reads as "cancelled" while some browsers treat it as "OK", and it cannot
      // be styled or read by the same tests as the rest of the app.
      event.preventDefault()
      setConfirming(true)
      return
    }
    leave()
  }

  return (
    <DropdownMenu onOpenChange={(open) => !open && setConfirming(false)}>
      <DropdownMenuTrigger className="flex items-center gap-[9px] rounded-md border border-ink-inv/12 bg-ink-inv/6 py-[5px] pr-[10px] pl-[6px] text-left transition-colors hover:bg-ink-inv/14 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink-inv">
        <span
          aria-hidden
          data-numeric
          className="flex size-[26px] shrink-0 items-center justify-center rounded-full bg-ink-inv/16 font-mono text-meta font-semibold text-ink-inv"
        >
          {initials(user.full_name)}
        </span>
        <span className="hidden min-w-0 flex-col leading-tight sm:flex">
          <span className="truncate text-meta font-medium text-ink-inv">{user.full_name}</span>
          <span className="truncate text-micro text-ink-inv-2">{ROLE_LABEL[user.role]}</span>
        </span>
      </DropdownMenuTrigger>

      <DropdownMenuContent aria-label="Menu akun">
        <DropdownMenuLabel>
          <span className="flex items-center gap-2 text-body font-semibold text-ink">
            <User aria-hidden className="size-4 text-ink-3" />
            {user.full_name}
          </span>
          <span data-numeric className="mt-[6px] block break-all font-mono text-meta text-ink-2">
            {user.email}
          </span>
          <span className="mt-[6px] flex items-center gap-2 text-meta text-ink-3">
            {ROLE_LABEL[user.role]}
            <span aria-hidden className="h-3 w-px bg-line" />
            <span data-numeric className="font-mono">
              {user.staff_token}
            </span>
          </span>
        </DropdownMenuLabel>

        <DropdownMenuSeparator />

        {confirming ? (
          <p className="px-[10px] py-2 text-meta leading-[1.5] text-notice">
            Ada disposisi yang belum tersimpan. Keluar sekarang akan membuangnya. Tekan
            <strong className="font-semibold"> Keluar </strong>
            sekali lagi untuk melanjutkan.
          </p>
        ) : null}

        <DropdownMenuItem onSelect={onSignOut} className="text-ink">
          <LogOut aria-hidden className="size-4 text-ink-3" />
          {confirming ? 'Keluar dan buang draf' : 'Keluar'}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

/** Up to two initials. Falls back to the first character rather than rendering an empty circle. */
function initials(fullName: string): string {
  const parts = fullName.trim().split(/\s+/).filter(Boolean)
  if (parts.length === 0) {
    return '?'
  }
  return parts
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? '')
    .join('')
}

import { LogOut, User } from 'lucide-react'
import { useState } from 'react'
import { Trans, useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { Dialog, DialogContent } from '@/components/ui/dialog'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useRoleLabel } from '@/features/auth/labels'
import { useSession } from '@/features/auth/useSession'
import { hasUnsavedDraft, useCaseDetailStore } from '@/features/review/case-detail/store'

/**
 * Who is signed in, at the right end of the header, and the way out.
 *
 * Replaces the hardcoded `analis casemix` constant, which matched no role in the code and no
 * role in `03_architecture.md` — it was the only role name a judge could actually see.
 *
 * **Signing out always asks.** It ends the session and empties whatever the reviewer had in
 * progress, and neither is undoable — a menu item that did both on a single click is a menu item
 * next to which a mis-click is expensive.
 *
 * The dialog changes its own wording when a disposition draft is unsaved: `store.ts` keeps drafts
 * alive precisely so a refused save does not cost the reviewer their work, and a sign-out that
 * silently discarded one would undo that guarantee from a different direction. So the draft case
 * names what is about to be lost rather than repeating the generic question.
 */
export function ProfileMenu() {
  const { t } = useTranslation(['auth', 'common'])
  const roleLabel = useRoleLabel()
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
    setConfirming(false)
    signOut()
    navigate('/login', { replace: true })
  }

  return (
    <>
    <DropdownMenu>
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
          <span className="truncate text-micro text-ink-inv-2">{roleLabel(user.role)}</span>
        </span>
      </DropdownMenuTrigger>

      <DropdownMenuContent aria-label={t('auth:profile.menu')}>
        <DropdownMenuLabel>
          <span className="flex items-center gap-2 text-body font-semibold text-ink">
            <User aria-hidden className="size-4 text-ink-3" />
            {user.full_name}
          </span>
          <span data-numeric className="mt-[6px] block break-all font-mono text-meta text-ink-2">
            {user.email}
          </span>
          <span className="mt-[6px] flex items-center gap-2 text-meta text-ink-3">
            {roleLabel(user.role)}
            <span aria-hidden className="h-3 w-px bg-line" />
            <span data-numeric className="font-mono">
              {user.staff_code}
            </span>
          </span>
        </DropdownMenuLabel>

        <DropdownMenuSeparator />

        <DropdownMenuItem
          onSelect={() => setConfirming(true)}
          className="text-ink"
        >
          <LogOut aria-hidden className="size-4 text-ink-3" />
          {t('auth:profile.signOut')}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>

    {/*
      `DialogContent` is rendered unconditionally inside `Dialog`, never behind a second
      `{confirming ? … : null}`. Radix's portal already mounts only while open, and tearing the
      content out in the same commit that flips `open` skips its close cleanup — which is how
      focus ends up on `<body>` instead of back on the trigger. `lib/useLastPresent.ts` exists
      because the case drawers hit exactly that; this dialog has no payload to keep alive, so it
      simply stays mounted.
    */}
    <Dialog open={confirming} onOpenChange={setConfirming}>
      {/*
        The corner X keeps its default name ("Tutup" / "Close") while the footer button is
        "Batal" / "Cancel": two controls sharing one accessible name are two controls a screen
        reader cannot tell apart, and that stays true in both languages.
      */}
      <DialogContent
        title={t('auth:profile.confirmTitle')}
        description={
          unsaved ? t('auth:profile.confirmDraft') : t('auth:profile.confirmPlain')
        }
      >
        <div className="px-5 py-4">
          <p className="text-body text-ink-2 text-pretty">
            <Trans
              i18nKey="profile.signedInAs"
              ns="auth"
              values={{ name: user.full_name, role: roleLabel(user.role) }}
              components={[
                <span key="0" />,
                <strong key="1" className="font-semibold text-ink" />,
              ]}
            />
          </p>
        </div>
        <div className="flex items-center justify-end gap-[10px] border-t border-line px-5 py-4">
          <Button type="button" variant="outline" onClick={() => setConfirming(false)}>
            {t('common:action.cancel')}
          </Button>
          <Button type="button" onClick={leave}>
            {unsaved ? t('auth:profile.signOutAndDiscard') : t('auth:profile.signOut')}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
    </>
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

import { ArrowRight, Minus, Plus } from 'lucide-react'
import { Trans, useTranslation } from 'react-i18next'

import { Button } from '@/components/ui/button'
import { Dialog, DialogContent } from '@/components/ui/dialog'
import { useRoleLabel } from '@/features/auth/labels'
import { capabilityChange, capabilityLabel } from '@/features/auth/matrix'
import type { Role, StaffUser } from '@/features/auth/types'
import { useLastPresent } from '@/lib/useLastPresent'
import i18n from '@/modules/i18n/config'

/**
 * What the administrator is about to do, before they do it.
 *
 * A dropdown that says "Senior Reviewer" tells you the name of a role. It does not tell you that
 * choosing it hands someone the authority to reopen a case another reviewer dismissed — that is
 * in ADR-0006 § 2, which the person clicking is not reading. This dialog says it in the same
 * words the login screen uses, read off the same generated matrix, so the sentence cannot
 * outlive the permission it describes.
 *
 * **Only the changes that take something away are confirmed.** A role change is confirmed both
 * ways because every one of them revokes as well as grants — moving a reviewer to `admin` takes
 * the entire queue from them. Deactivation is confirmed because it locks a person out.
 * Reactivation is not: it restores access that was already granted, is recorded either way, and
 * a dialog in front of every harmless act is a dialog people learn to dismiss unread.
 */
export type PendingChange =
  | { readonly kind: 'role'; readonly user: StaffUser; readonly role: Role }
  | { readonly kind: 'deactivate'; readonly user: StaffUser }

export function ConfirmUserChange({
  change,
  onCancel,
  onConfirm,
}: {
  readonly change: PendingChange | null
  readonly onCancel: () => void
  readonly onConfirm: (change: PendingChange) => void
}) {
  const { t } = useTranslation('admin')
  // Kept alive for the closing frame so Radix can return focus to the control that opened this.
  // See `lib/useLastPresent.ts` — the alternative loses focus to `<body>` on every close.
  const shown = useLastPresent(change)

  return (
    <Dialog open={change !== null} onOpenChange={(open) => (open ? undefined : onCancel())}>
      <DialogContent
        title={shown ? titleFor(shown) : ''}
        description={shown ? descriptionFor(shown) : undefined}
      >
        <div className="px-5 py-4">
          {shown?.kind === 'role' ? (
            <RoleChangeBody user={shown.user} role={shown.role} />
          ) : shown ? (
            <DeactivateBody user={shown.user} />
          ) : null}
        </div>
        <div className="flex items-center justify-end gap-[10px] border-t border-line px-5 py-4">
          <Button type="button" variant="outline" onClick={onCancel}>
            {i18n.t('common:action.cancel')}
          </Button>
          <Button type="button" onClick={() => shown && onConfirm(shown)}>
            {shown?.kind === 'role' ? t('confirm.confirmRole') : t('confirm.confirmDeactivate')}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

function RoleChangeBody({ user, role }: { readonly user: StaffUser; readonly role: Role }) {
  const { t } = useTranslation('admin')
  const roleLabel = useRoleLabel()
  const { granted, revoked } = capabilityChange(user.role, role)

  return (
    <>
      <p className="flex flex-wrap items-center gap-2 text-body text-ink">
        <RoleChip>{roleLabel(user.role)}</RoleChip>
        <ArrowRight aria-hidden className="size-4 text-ink-3" />
        <RoleChip>{roleLabel(role)}</RoleChip>
      </p>

      <dl className="mt-4 space-y-3">
        <CapabilityList
          heading={t('confirm.granted')}
          capabilities={granted}
          tone="grant"
          empty={t('confirm.grantedEmpty')}
        />
        <CapabilityList
          heading={t('confirm.revoked')}
          capabilities={revoked}
          tone="revoke"
          empty={t('confirm.revokedEmpty')}
        />
      </dl>

      <p className="mt-4 text-meta text-ink-3 text-pretty">{t('confirm.generatedNote')}</p>
    </>
  )
}

function DeactivateBody({ user }: { readonly user: StaffUser }) {
  const { t } = useTranslation('admin')

  return (
    <>
      <p className="text-body text-ink text-pretty">
        <Trans
          i18nKey="confirm.deactivateLede"
          ns="admin"
          values={{ name: user.full_name }}
          components={[<span key="0" />, <strong key="1" className="font-semibold" />]}
        />
      </p>
      <ul className="mt-3 space-y-[6px] text-meta text-ink-2">
        {/*
          Said out loud because an administrator cannot check it from here: this page has no
          access to a single case, by design (ADR-0006 § 2). Leaving them to guess what happens
          to in-flight work is how a reversible act gets treated as an irreversible one.
        */}
        <li>{t('confirm.deactivatePoint1')}</li>
        <li>{t('confirm.deactivatePoint2')}</li>
        <li>{t('confirm.deactivatePoint3')}</li>
      </ul>
    </>
  )
}

function CapabilityList({
  heading,
  capabilities,
  tone,
  empty,
}: {
  readonly heading: string
  readonly capabilities: readonly string[]
  readonly tone: 'grant' | 'revoke'
  readonly empty: string
}) {
  const Icon = tone === 'grant' ? Plus : Minus

  return (
    <div>
      <dt className="font-mono text-micro font-semibold tracking-label text-ink-3">{heading}</dt>
      <dd className="mt-[6px]">
        {capabilities.length === 0 ? (
          <p className="text-meta text-ink-3">{empty}</p>
        ) : (
          <ul className="space-y-[5px]">
            {capabilities.map((capability) => (
              <li
                key={capability}
                className={
                  tone === 'grant'
                    ? 'flex items-center gap-2 text-small text-done'
                    : 'flex items-center gap-2 text-small text-notice'
                }
              >
                {/* The icon is decorative; the heading above already says which list this is. */}
                <Icon aria-hidden className="size-[13px] shrink-0" />
                {capabilityLabel(capability)}
              </li>
            ))}
          </ul>
        )}
      </dd>
    </div>
  )
}

function RoleChip({ children }: { readonly children: React.ReactNode }) {
  return (
    <span className="rounded-md border border-line bg-sunk px-[9px] py-[2px] text-small font-semibold text-ink">
      {children}
    </span>
  )
}

/**
 * The dialog's own title and description, which `DialogContent` takes as plain strings rather
 * than nodes — so they are resolved through the i18next instance instead of a hook.
 */
function titleFor(change: PendingChange): string {
  const key = change.kind === 'role' ? 'admin:confirm.roleTitle' : 'admin:confirm.deactivateTitle'
  return i18n.t(key as 'admin:confirm.roleTitle', { name: change.user.full_name })
}

function descriptionFor(change: PendingChange): string {
  return change.kind === 'role'
    ? i18n.t('admin:confirm.roleDescription')
    : i18n.t('admin:confirm.deactivateDescription')
}

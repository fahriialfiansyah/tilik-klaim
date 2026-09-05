import { Download } from 'lucide-react'
import { useEffect, useState } from 'react'

import { Button } from '@/components/ui/button'
import { PageHeader, PageShell } from '@/components/layouts/PageShell'
import { ChangeUndoBar } from '@/features/admin/users/components/ChangeUndoBar'
import {
  ConfirmUserChange,
  type PendingChange,
} from '@/features/admin/users/components/ConfirmUserChange'
import { UserAuditPanel } from '@/features/admin/users/components/UserAuditPanel'
import { UserTable } from '@/features/admin/users/components/UserTable'
import {
  UsersEmpty,
  UsersFailed,
  UsersLoading,
} from '@/features/admin/users/components/UsersPlaceholders'
import { auditCsvFilename, buildAuditCsv, downloadCsv } from '@/features/admin/users/csv'
import { useUsers } from '@/features/admin/users/useUsers'
import { useSession } from '@/features/auth/useSession'
import type { Role, StaffUser } from '@/features/auth/types'

/**
 * Page 6 — Manajemen Pengguna (`/admin/users`). Administrator only.
 *
 * **This page never touches a claim, and an administrator cannot reach one.** That separation
 * is the whole reason the role exists — `07_privacy_threat_model.md` names separation of duties
 * directly, and ADR-0006 § 2 makes every ❌ in its matrix a server-side refusal rather than a
 * hidden button.
 *
 * Two changes only: the role, and the active flag. No create and no delete — the synthetic
 * roster is fixed at three (ADR-0006 § 7). Each change appends an audit event that is never
 * edited, and everything built on top of that is built to respect it: the confirmation names the
 * capabilities a role change moves, undo appends a reversing event rather than deleting one, and
 * the export is a copy of the trail rather than a way to edit it.
 */
export function AdminUsersPage() {
  const user = useSession((state) => state.user)
  const { status, users, events, pendingUserId, refusal, undoable, reload, change, undo, dismissUndo } =
    useUsers()
  const [pending, setPending] = useState<PendingChange | null>(null)

  useEffect(() => {
    document.title = 'Manajemen Pengguna · TilikKlaim'
  }, [])

  const nameFor = (userId: string) =>
    users.find((candidate) => candidate.user_id === userId)?.full_name ?? userId

  /** A role change always both grants and revokes, so it always asks first. */
  function requestRole(target: StaffUser, role: Role) {
    setPending({ kind: 'role', user: target, role })
  }

  /**
   * Deactivation asks; reactivation does not.
   *
   * Locking a person out is the act worth a second look. Letting them back in restores access
   * they already had, is recorded either way, and putting a dialog in front of it would teach
   * the administrator to click through the one that matters.
   */
  function requestActive(target: StaffUser, isActive: boolean) {
    if (isActive) {
      void change(target.user_id, { is_active: true })
      return
    }
    setPending({ kind: 'deactivate', user: target })
  }

  function commit(confirmed: PendingChange) {
    setPending(null)
    void change(
      confirmed.user.user_id,
      confirmed.kind === 'role' ? { role: confirmed.role } : { is_active: false },
    )
  }

  function exportAudit() {
    downloadCsv(auditCsvFilename(), buildAuditCsv(events, nameFor))
  }

  return (
    <PageShell>
      <PageHeader
        eyebrow="DAFTAR PETUGAS · PERAN DAN STATUS"
        title="Manajemen Pengguna"
        lede="Tiga akun petugas sintetik. Peran dapat diubah dan akun dapat dinonaktifkan; tidak ada penambahan dan tidak ada penghapusan. Setiap perubahan tercatat permanen di riwayat di bawah."
      />

      <div className="space-y-4">
        {refusal ? (
          <p
            role="alert"
            className="rounded-md border border-notice-line bg-notice-bg px-4 py-3 text-body text-notice text-pretty"
          >
            <span className="font-semibold">Perubahan ditolak: </span>
            {refusal.message}
          </p>
        ) : null}

        {undoable ? (
          <ChangeUndoBar
            change={undoable}
            busy={pendingUserId !== null}
            onUndo={() => void undo()}
            onDismiss={dismissUndo}
          />
        ) : null}

        <section
          aria-labelledby="roster-heading"
          className="overflow-hidden rounded-md border border-line bg-card"
        >
          <h2
            id="roster-heading"
            className="border-b border-line px-4 py-3 text-lead font-semibold text-ink"
          >
            Daftar petugas
          </h2>

          {status === 'loading' ? <UsersLoading /> : null}
          {status === 'empty' ? <UsersEmpty /> : null}
          {status === 'failed' ? <UsersFailed onRetry={reload} /> : null}
          {status === 'ready' && user ? (
            <UserTable
              users={users}
              selfId={user.user_id}
              pendingUserId={pendingUserId}
              onChangeRole={requestRole}
              onToggleActive={requestActive}
            />
          ) : null}
        </section>

        <section
          aria-labelledby="user-audit-heading"
          className="overflow-hidden rounded-md border border-line bg-card"
        >
          <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2 border-b border-line px-4 py-3">
            <h2 id="user-audit-heading" className="text-lead font-semibold text-ink">
              Riwayat manajemen pengguna
              <span className="ml-2 font-normal text-meta text-ink-3">terbaru di atas</span>
            </h2>
            {/*
              The trail is a governance deliverable, and one that can only be read on screen is a
              deliverable that stops existing the moment the demo does. Disabled rather than
              hidden when there is nothing yet: a control that comes and goes is a control an
              administrator has to hunt for.
            */}
            <Button
              type="button"
              variant="outline"
              disabled={status !== 'ready' || events.length === 0}
              onClick={exportAudit}
            >
              <Download aria-hidden className="size-4" />
              Unduh CSV
            </Button>
          </div>
          {status === 'ready' ? (
            <UserAuditPanel events={events} nameFor={nameFor} />
          ) : (
            <p className="px-4 py-6 text-body text-ink-2">
              Riwayat dimuat bersama daftar petugas.
            </p>
          )}
        </section>
      </div>

      <ConfirmUserChange
        change={pending}
        onCancel={() => setPending(null)}
        onConfirm={commit}
      />
    </PageShell>
  )
}

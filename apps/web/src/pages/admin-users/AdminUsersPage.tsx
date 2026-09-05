import { useEffect } from 'react'

import { PageHeader, PageShell } from '@/components/layouts/PageShell'
import { UserAuditPanel } from '@/features/admin/users/components/UserAuditPanel'
import { UserTable } from '@/features/admin/users/components/UserTable'
import {
  UsersEmpty,
  UsersFailed,
  UsersLoading,
} from '@/features/admin/users/components/UsersPlaceholders'
import { useUsers } from '@/features/admin/users/useUsers'
import { useSession } from '@/features/auth/useSession'

/**
 * Page 6 — Manajemen Pengguna (`/admin/users`). Administrator only.
 *
 * **This page never touches a claim, and an administrator cannot reach one.** That separation
 * is the whole reason the role exists — `07_privacy_threat_model.md` names separation of duties
 * directly, and ADR-0006 § 2 makes every ❌ in its matrix a server-side refusal rather than a
 * hidden button.
 *
 * Two changes only: the role, and the active flag. No create and no delete — the synthetic
 * roster is fixed at three. Each change appends an audit event that is never edited.
 */
export function AdminUsersPage() {
  const user = useSession((state) => state.user)
  const { status, users, events, pendingUserId, refusal, reload, change } = useUsers()

  useEffect(() => {
    document.title = 'Manajemen Pengguna — TilikKlaim'
  }, [])

  const nameFor = (userId: string) =>
    users.find((candidate) => candidate.user_id === userId)?.full_name ?? userId

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
            <span className="font-semibold">Perubahan ditolak — </span>
            {refusal.message}
          </p>
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
              onChangeRole={(userId, role) => void change(userId, { role })}
              onToggleActive={(userId, isActive) => void change(userId, { is_active: isActive })}
            />
          ) : null}
        </section>

        <section
          aria-labelledby="user-audit-heading"
          className="overflow-hidden rounded-md border border-line bg-card"
        >
          <h2
            id="user-audit-heading"
            className="border-b border-line px-4 py-3 text-lead font-semibold text-ink"
          >
            Riwayat manajemen pengguna
            <span className="ml-2 font-normal text-meta text-ink-3">terbaru di atas</span>
          </h2>
          {status === 'ready' ? (
            <UserAuditPanel events={events} nameFor={nameFor} />
          ) : (
            <p className="px-4 py-6 text-body text-ink-2">
              Riwayat dimuat bersama daftar petugas.
            </p>
          )}
        </section>
      </div>
    </PageShell>
  )
}

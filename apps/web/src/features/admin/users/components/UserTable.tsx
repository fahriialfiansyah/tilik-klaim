import { PerfectScrollArea } from '@/components/wrappers/PerfectScrollArea'
import { COLUMNS } from '@/features/admin/users/labels'
import { formatSignedIn } from '@/features/admin/users/format'
import { ROLE_LABEL } from '@/features/auth/labels'
import { ROLES, type Role, type StaffUser } from '@/features/auth/types'
import { cn } from '@/lib/utils'

/**
 * The roster as a real `<table>` — `<th scope>`, one row per account, keyboard-complete.
 *
 * Both controls are native: a `<select>` for the role and a checkbox for the active flag. They
 * carry their own labels, keyboard behaviour and focus rings, and nothing here re-implements
 * any of it. A visually hidden control styled to look like something else is a defect this
 * codebase has already paid for once.
 *
 * `self` marks the signed-in administrator's own row. They may not change their own role or
 * deactivate themselves — refused on the server with `USER_SELF_MODIFICATION_REFUSED`; the
 * disabled controls here only save them the click, and the reason is said out loud rather than
 * left to a greyed-out box.
 */
export function UserTable({
  users,
  selfId,
  pendingUserId,
  onChangeRole,
  onToggleActive,
}: {
  readonly users: readonly StaffUser[]
  readonly selfId: string
  readonly pendingUserId: string | null
  readonly onChangeRole: (userId: string, role: Role) => void
  readonly onToggleActive: (userId: string, isActive: boolean) => void
}) {
  return (
    <PerfectScrollArea className="max-h-[520px]">
      <table className="w-full border-collapse text-left">
        <caption className="sr-only">
          Daftar petugas sintetik, perannya, dan statusnya.
        </caption>
        <thead>
          <tr className="bg-sunk">
            {COLUMNS.map((column) => (
              <th
                key={column}
                scope="col"
                className="border-b border-line px-3 py-[10px] font-mono text-micro font-semibold tracking-label text-ink-3"
              >
                {column === 'Tindakan' ? <span className="sr-only">{column}</span> : column}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {users.map((user) => {
            const isSelf = user.user_id === selfId
            const busy = pendingUserId === user.user_id
            return (
              <tr key={user.user_id} className="border-b border-line last:border-b-0">
                <th scope="row" className="px-3 py-[11px] text-body font-medium text-ink">
                  {user.full_name}
                  {isSelf ? (
                    <span className="ml-2 rounded-sm bg-brand-soft px-[6px] py-[1px] text-micro font-semibold text-brand">
                      ANDA
                    </span>
                  ) : null}
                </th>
                <td data-numeric className="px-3 py-[11px] font-mono text-meta text-ink-2">
                  {user.staff_token}
                </td>
                <td data-numeric className="px-3 py-[11px] font-mono text-meta break-all text-ink-2">
                  {user.email}
                </td>
                <td className="px-3 py-[11px]">
                  <label className="sr-only" htmlFor={`role-${user.user_id}`}>
                    Peran untuk {user.full_name}
                  </label>
                  <select
                    id={`role-${user.user_id}`}
                    value={user.role}
                    disabled={isSelf || busy}
                    onChange={(event) => onChangeRole(user.user_id, event.target.value as Role)}
                    className="h-8 rounded-md border border-line bg-card px-2 text-small text-ink outline-none focus-visible:border-brand focus-visible:ring-2 focus-visible:ring-ring/40 disabled:opacity-60"
                  >
                    {ROLES.map((role) => (
                      <option key={role} value={role}>
                        {ROLE_LABEL[role]}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="px-3 py-[11px]">
                  <label className="flex w-fit items-center gap-2 text-small">
                    <input
                      type="checkbox"
                      checked={user.is_active}
                      disabled={isSelf || busy}
                      onChange={(event) => onToggleActive(user.user_id, event.target.checked)}
                      className="size-4 accent-[var(--a-1)] disabled:opacity-60"
                    />
                    {/* Status is never colour alone — the word is the label. */}
                    <span
                      className={cn(
                        'font-medium',
                        user.is_active ? 'text-done' : 'text-ink-3',
                      )}
                    >
                      {user.is_active ? 'Aktif' : 'Nonaktif'}
                    </span>
                  </label>
                </td>
                <td data-numeric className="px-3 py-[11px] font-mono text-meta text-ink-2">
                  {formatSignedIn(user.last_signed_in_at)}
                </td>
                <td className="px-3 py-[11px] text-meta text-ink-3">
                  {isSelf ? 'Akun sendiri tidak dapat diubah' : busy ? 'Menyimpan…' : null}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </PerfectScrollArea>
  )
}

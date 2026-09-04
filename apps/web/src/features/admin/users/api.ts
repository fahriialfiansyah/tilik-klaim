import type {
  UserAuditResponse,
  UserListResponse,
  UserUpdateResponse,
} from '@/features/admin/users/types'
import type { Role } from '@/features/auth/types'
import { request } from '@/lib/http'

/**
 * The two actor headers travel automatically from the signed-in persona (`src/lib/http.ts`),
 * so nothing here attaches them. The server refuses a non-admin caller regardless of what this
 * module does — hiding the page is a courtesy, not the control.
 */
export async function fetchUsers(): Promise<UserListResponse> {
  return request<UserListResponse>('/users')
}

export async function fetchUserAudit(): Promise<UserAuditResponse> {
  return request<UserAuditResponse>('/users/audit')
}

/** A role change, an active-flag change, or both. Omitted fields are left alone. */
export async function updateUser(
  userId: string,
  change: { readonly role?: Role; readonly is_active?: boolean },
): Promise<UserUpdateResponse> {
  return request<UserUpdateResponse>(`/users/${encodeURIComponent(userId)}`, {
    method: 'PATCH',
    body: JSON.stringify(change),
  })
}

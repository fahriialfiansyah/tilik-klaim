import type { Role } from '@/features/auth/types'

/** Role labels. Indonesian, working language, never a job title nobody uses out loud. */
export const ROLE_LABEL: Readonly<Record<Role, string>> = {
  reviewer: 'Peninjau',
  senior_reviewer: 'Peninjau Senior',
  admin: 'Administrator',
}

/** One line each, shown beside the role on the login cards and in the admin table. */
export const ROLE_DESCRIPTION: Readonly<Record<Role, string>> = {
  reviewer: 'Menilai kasus dan mencatat disposisi.',
  senior_reviewer: 'Sama, ditambah membuka kembali kasus yang sudah ditolak.',
  admin: 'Mengelola pengguna. Tidak pernah menyentuh kasus klaim.',
}

export const ACTIVE_LABEL = { true: 'Aktif', false: 'Nonaktif' } as const

import { useTranslation } from 'react-i18next'

import type { Role } from '@/features/auth/types'
import i18n from '@/modules/i18n/config'

/**
 * Role names, as the reader's language writes them.
 *
 * These were a plain `Record<Role, string>` while the product spoke one language. They are hooks
 * now for one reason: a constant is read once at module load, so a map of Indonesian strings
 * would keep rendering Indonesian after the header switch — the export would have to be re-read
 * to change, and nothing re-reads a module.
 *
 * The shape is deliberately still "give me a `Role`, get a string", so every call site reads the
 * same as it did. What changed is *when* the lookup happens, not what it looks like.
 */
export function useRoleLabel(): (role: Role) => string {
  const { t } = useTranslation('auth')
  return (role) => t(`role.${role}` as 'role.reviewer')
}

/** One line each, shown beside the role on the login cards and in the admin table. */
export function useRoleDescription(): (role: Role) => string {
  const { t } = useTranslation('auth')
  return (role) => t(`roleDescription.${role}` as 'roleDescription.reviewer')
}

/** Whether an account is active, in words rather than a colour. */
export function useActiveLabel(): (active: boolean) => string {
  const { t } = useTranslation('auth')
  return (active) => (active ? t('active.true') : t('active.false'))
}

/**
 * The same lookups outside React.
 *
 * `csv.ts` builds an export file and `useUsers.ts` composes a live-region sentence; neither is
 * a component, so neither may call a hook. They read the running i18next instance directly,
 * which resolves in whatever language is active at the moment they are called — a CSV
 * downloaded from an English screen is an English CSV.
 */
export function roleLabel(role: Role): string {
  return i18n.t(`auth:role.${role}` as 'auth:role.reviewer')
}

import { NEVER_SIGNED_IN } from '@/features/admin/users/labels'

/**
 * A timestamp a person can read, with aligned digits.
 *
 * `null` is *not* rendered as an em-dash: "belum pernah masuk" is a fact about the account, and
 * a dash reads as missing data. The distinction matters on the one column an administrator
 * would use to notice an account nobody uses.
 */
export function formatSignedIn(value: string | null): string {
  if (value === null) {
    return NEVER_SIGNED_IN
  }
  return formatStamp(value)
}

export function formatStamp(value: string): string {
  const when = new Date(value)
  if (Number.isNaN(when.getTime())) {
    return value
  }
  return new Intl.DateTimeFormat('id-ID', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(when)
}

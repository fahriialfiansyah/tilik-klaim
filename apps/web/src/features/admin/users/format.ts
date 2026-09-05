import { NEVER_SIGNED_IN } from '@/features/admin/users/labels'
import { formatDateTime } from '@/lib/datetime'

/**
 * A timestamp a person can read, with aligned digits.
 *
 * `null` is *not* rendered as an em-dash: "belum pernah masuk" is a fact about the account, and
 * a dash reads as missing data. The distinction matters on the one column an administrator
 * would use to notice an account nobody uses.
 *
 * The formatting itself belongs to `lib/datetime.ts` — pinned to `Asia/Jakarta` and labelled
 * WIB, because a sign-in time read on its own with no zone is a number an administrator cannot
 * act on.
 */
export function formatSignedIn(value: string | null): string {
  if (value === null) {
    return NEVER_SIGNED_IN
  }
  return formatDateTime(value)
}

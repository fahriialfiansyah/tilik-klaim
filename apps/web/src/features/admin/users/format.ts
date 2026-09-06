import { formatDateTime } from '@/lib/datetime'
import i18n from '@/modules/i18n/config'

/**
 * A timestamp a person can read, with aligned digits.
 *
 * `null` is *not* rendered as an em-dash: "never signed in" is a fact about the account, and a
 * dash reads as missing data. The distinction matters on the one column an administrator
 * would use to notice an account nobody uses.
 *
 * The formatting itself belongs to `lib/datetime.ts` — pinned to `Asia/Jakarta` and labelled
 * WIB, because a sign-in time read on its own with no zone is a number an administrator cannot
 * act on.
 */
export function formatSignedIn(value: string | null): string {
  if (value === null) {
    return i18n.t('admin:neverSignedIn')
  }
  return formatDateTime(value)
}

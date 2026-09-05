/**
 * Every timestamp this app prints, in one place and in one time zone.
 *
 * **The zone is pinned, not inherited.** `Intl` defaults to the *viewer's* zone, which meant a
 * case timestamp read one way on a laptop set to Jakarta and another on one set to Singapore —
 * with nothing on screen saying which. For a review tool whose audit trail is the product, a
 * clock that quietly changes meaning per machine is a defect, and labelling such a value "WIB"
 * would have turned it into a false one.
 *
 * **The label follows the reading, not the zone.** `formatDateTime` carries `WIB` because it is
 * read on its own — an audit entry, a last sign-in — and a bare stamp with no zone is the
 * ambiguity this module exists to remove. `formatTime` does not, because it is only ever read
 * beneath a date that already established the day; repeating `WIB` on every tick of a swimlane
 * axis is noise, not precision.
 *
 * `timeZoneName: 'short'` rather than a concatenated `' WIB'`: `Intl` derives the abbreviation
 * from the zone, so changing `APP_TIME_ZONE` to `Asia/Makassar` renders WITA instead of leaving
 * a hardcoded label that has become a lie.
 */

/** Where this hospital is. One constant, so a zone change cannot be applied to only half the app. */
export const APP_TIME_ZONE = 'Asia/Jakarta'

const DATE_TIME = new Intl.DateTimeFormat('id-ID', {
  timeZone: APP_TIME_ZONE,
  day: '2-digit',
  month: 'short',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
  timeZoneName: 'short',
})

// No zone label: a date has no clock to qualify. The zone is still pinned, because which *day*
// an instant falls on depends on it — 2026-09-05T17:30Z is already the 6th in Jakarta.
const DATE = new Intl.DateTimeFormat('id-ID', {
  timeZone: APP_TIME_ZONE,
  day: '2-digit',
  month: 'short',
  year: 'numeric',
})

const TIME = new Intl.DateTimeFormat('id-ID', {
  timeZone: APP_TIME_ZONE,
  hour: '2-digit',
  minute: '2-digit',
})

/** An em dash for anything unreadable — never the string `Invalid Date`. */
export const NO_STAMP = '—'

/** `null` for anything unreadable, so a caller can tell "absent" from "malformed". */
export function parseStamp(isoTimestamp: string | null | undefined): Date | null {
  if (!isoTimestamp) {
    return null
  }
  const value = new Date(isoTimestamp)
  return Number.isNaN(value.getTime()) ? null : value
}

/** `05 Sep 2026, 20.45 WIB` — a stamp that has to survive being read on its own. */
export function formatDateTime(isoTimestamp: string | null | undefined): string {
  const value = parseStamp(isoTimestamp)
  return value ? DATE_TIME.format(value) : NO_STAMP
}

/** `05 Sep 2026`. */
export function formatDate(isoTimestamp: string | null | undefined): string {
  const value = parseStamp(isoTimestamp)
  return value ? DATE.format(value) : NO_STAMP
}

/** `20.45` — for a clock reading under a date that is already on screen. */
export function formatTime(isoTimestamp: string | null | undefined): string {
  const value = parseStamp(isoTimestamp)
  return value ? TIME.format(value) : NO_STAMP
}

/**
 * `WIB` — derived from `APP_TIME_ZONE`, never typed out.
 *
 * For the one caller that prints a range and needs the abbreviation once at the end rather than
 * on both halves. Read from `Intl` for the same reason `timeZoneName: 'short'` is used above: a
 * hardcoded label survives a zone change and becomes wrong.
 */
export const ZONE_LABEL: string =
  DATE_TIME.formatToParts(new Date()).find((part) => part.type === 'timeZoneName')?.value ?? ''

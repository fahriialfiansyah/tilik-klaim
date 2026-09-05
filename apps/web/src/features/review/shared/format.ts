const HOURS_PER_DAY = 24
const MS_PER_HOUR = 3_600_000

const AMOUNT = new Intl.NumberFormat('id-ID', {
  style: 'currency',
  currency: 'IDR',
  maximumFractionDigits: 0,
})

/** Claim amounts are synthetic and illustrative; they still have to line up between rows. */
export function formatAmount(amount: string): string {
  const value = Number(amount)
  return Number.isFinite(value) ? AMOUNT.format(value) : '-'
}

/** How long a case has been waiting, in working language. */
export function formatAge(isoTimestamp: string): string {
  const hours = (Date.now() - new Date(isoTimestamp).getTime()) / MS_PER_HOUR
  if (hours < 1) {
    return '< 1 jam'
  }
  if (hours < HOURS_PER_DAY) {
    return `${Math.floor(hours)} jam`
  }
  return `${Math.floor(hours / HOURS_PER_DAY)} hari`
}

export function formatHours(hours: number): string {
  return hours < 1 ? '< 1' : String(Math.round(hours))
}

/**
 * Timestamps live in `lib/datetime.ts` and are re-exported here so this module stays the one
 * import a review screen needs. They are pinned to `Asia/Jakarta` and `formatDateTime` says WIB
 * out loud — see that module for why the zone is not the viewer's.
 */
export { formatDate, formatDateTime, formatTime } from '@/lib/datetime'

import { ZONE_LABEL, formatDate, formatDateTime, formatTime, parseStamp } from '@/lib/datetime'
/**
 * The encounter window.
 *
 * An episode with no recorded end is written as open rather than as a range ending at its own
 * start — a zero-length visit is a claim the data does not make.
 */
export function formatDateRange(start: string, end: string | null | undefined): string {
  if (!parseStamp(start)) {
    return '-'
  }
  if (!parseStamp(end)) {
    return `${formatDateTime(start)}, belum ditutup`
  }
  // Compared through the formatter rather than `Date.toDateString()`, which answers in the
  // *viewer's* zone: an episode from 23.00 to 01.00 WIB is one calendar day here and two on a
  // laptop set to Manila, and the reader would get a different sentence for the same stay.
  const sameDay = formatDate(start) === formatDate(end)
  return sameDay
    ? `${formatDate(start)} · ${formatTime(start)}-${formatTime(end)} ${ZONE_LABEL}`
    : `${formatDateTime(start)} s.d. ${formatDateTime(end)}`
}

const ISO_TIMESTAMP = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/

/**
 * Format a raw field value when, and only when, it is a timestamp.
 *
 * Resource panels and the comparison drawer show values "apa adanya", but an ISO string is the
 * transport encoding rather than the field itself. A reviewer comparing a procedure's time to a
 * billed line's should not have to convert one of them in their head — and reading one in UTC
 * while the rest of the screen is local is how two identical moments come to look hours apart.
 */
export function formatIfTimestamp(value: string): string {
  return ISO_TIMESTAMP.test(value) ? formatDateTime(value) : value
}

/**
 * Give a server message a full stop so it reads as a sentence beside our own.
 *
 * Error text arrives with and without trailing punctuation — the API's own `detail` usually has
 * it, a proxy's bare status line never does — and every failure banner on this app follows the
 * server's words with an explanation of its own. Without this the two run together as
 * "Gateway Timeout Tidak ada kejadian audit...".
 */
export function withStop(message: string): string {
  return /[.!?]$/.test(message.trim()) ? message : `${message}.`
}

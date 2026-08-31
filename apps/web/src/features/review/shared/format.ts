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
  return Number.isFinite(value) ? AMOUNT.format(value) : '—'
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

const DATE_TIME = new Intl.DateTimeFormat('id-ID', {
  day: '2-digit',
  month: 'short',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
})

const DATE = new Intl.DateTimeFormat('id-ID', {
  day: '2-digit',
  month: 'short',
  year: 'numeric',
})

const TIME = new Intl.DateTimeFormat('id-ID', { hour: '2-digit', minute: '2-digit' })

/** An unparseable timestamp renders as an em dash rather than "Invalid Date". */
function parse(isoTimestamp: string | null | undefined): Date | null {
  if (!isoTimestamp) {
    return null
  }
  const value = new Date(isoTimestamp)
  return Number.isNaN(value.getTime()) ? null : value
}

export function formatDateTime(isoTimestamp: string | null | undefined): string {
  const value = parse(isoTimestamp)
  return value ? DATE_TIME.format(value) : '—'
}

export function formatDate(isoTimestamp: string | null | undefined): string {
  const value = parse(isoTimestamp)
  return value ? DATE.format(value) : '—'
}

export function formatTime(isoTimestamp: string | null | undefined): string {
  const value = parse(isoTimestamp)
  return value ? TIME.format(value) : '—'
}

/**
 * The encounter window.
 *
 * An episode with no recorded end is written as open rather than as a range ending at its own
 * start — a zero-length visit is a claim the data does not make.
 */
export function formatDateRange(start: string, end: string | null | undefined): string {
  const from = parse(start)
  if (!from) {
    return '—'
  }
  const to = parse(end)
  if (!to) {
    return `${DATE_TIME.format(from)} — belum ditutup`
  }
  const sameDay = from.toDateString() === to.toDateString()
  return sameDay
    ? `${DATE.format(from)} · ${TIME.format(from)}–${TIME.format(to)}`
    : `${DATE_TIME.format(from)} — ${DATE_TIME.format(to)}`
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

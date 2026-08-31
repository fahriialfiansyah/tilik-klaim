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

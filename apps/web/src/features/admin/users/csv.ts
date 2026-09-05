import { EVENT_LABEL } from '@/features/admin/users/labels'
import type { UserAuditEvent } from '@/features/admin/users/types'
import { ROLE_LABEL } from '@/features/auth/labels'
import { isRole } from '@/features/auth/types'
import { formatDateTime } from '@/lib/datetime'

/**
 * The user-management trail as a file somebody can keep.
 *
 * `07_privacy_threat_model.md` § Governance deliverables owes a record of who was granted what.
 * A panel that can only be read on screen satisfies that in the room and nowhere else — an
 * auditor asking for the trail six months from now wants a file, not a screenshot.
 *
 * Built in working language, not raw storage values: `USER_ROLE_CHANGED` / `senior_reviewer` is
 * the shape the database keeps, and a governance artefact that has to be decoded before it can
 * be read is one nobody checks. The raw `event_id` rides along as the last column so a row can
 * still be traced back to the one it came from.
 */
export const AUDIT_CSV_HEADER = [
  'Waktu',
  'Kejadian',
  'Petugas',
  'Bidang',
  'Sebelum',
  'Sesudah',
  'Pelaku',
  'Peran pelaku',
  'ID kejadian',
] as const

/**
 * The stored field names, in working language.
 *
 * `role` and `is_active` are column names in Postgres. Leaving them raw put two English
 * identifiers in the middle of an otherwise Indonesian sheet, and asked the reader of a
 * governance record to know the schema before they could read it.
 */
const FIELD_LABEL: Readonly<Record<string, string>> = {
  role: 'Peran',
  is_active: 'Status aktif',
}

/** Formulae in a spreadsheet start with one of these. */
const FORMULA_PREFIXES = ['=', '+', '-', '@', '\t', '\r']

export function buildAuditCsv(
  events: readonly UserAuditEvent[],
  nameFor: (userId: string) => string,
): string {
  const rows = events.map((event) => [
    formatDateTime(event.occurred_at),
    EVENT_LABEL[event.event_kind] ?? event.event_kind,
    nameFor(event.target_user_id),
    FIELD_LABEL[event.field] ?? event.field,
    readable(event.value_before),
    readable(event.value_after),
    nameFor(event.actor_user_id),
    readableRole(event.actor_role),
    event.event_id,
  ])

  // CRLF, because a CSV opened in Excel on Windows is the realistic destination for this file.
  return [AUDIT_CSV_HEADER, ...rows].map((row) => row.map(cell).join(',')).join('\r\n')
}

/**
 * One CSV cell: RFC 4180 quoting, plus a guard against spreadsheet formula injection.
 *
 * The quoting half is ordinary. The guard is not, and it is here because this file is *exported
 * to be opened in Excel*: a cell beginning `=`, `+`, `-` or `@` is evaluated as a formula on
 * open, and `=HYPERLINK(...)` in a name field is a way to turn an audit export into an attack on
 * whoever reads it. Every value here comes from our own seeded roster today, which is exactly
 * the reason to fix it now — the guard has to already exist on the day a name stops being ours.
 *
 * Prefixed with a tab rather than stripped: the reader still sees the original text, and no
 * character of a governance record is silently discarded on the way out.
 */
function cell(value: string): string {
  const guarded = FORMULA_PREFIXES.some((prefix) => value.startsWith(prefix))
    ? `\t${value}`
    : value
  return `"${guarded.replaceAll('"', '""')}"`
}

/** Raw stored values become working language, the same way the on-screen panel reads them. */
function readable(value: string | null): string {
  if (value === null) {
    return ''
  }
  if (value === 'true') {
    return 'Aktif'
  }
  if (value === 'false') {
    return 'Nonaktif'
  }
  return isRole(value) ? ROLE_LABEL[value] : value
}

function readableRole(role: string): string {
  return isRole(role) ? ROLE_LABEL[role] : role
}

/** `riwayat-pengguna-2026-09-05.csv` — sortable, and says what it is without being opened. */
export function auditCsvFilename(now: Date = new Date()): string {
  const stamp = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Jakarta',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(now)
  return `riwayat-pengguna-${stamp}.csv`
}

/**
 * Hand the file to the browser.
 *
 * Two accommodations for Excel live here, and nowhere else — `buildAuditCsv` stays plain
 * RFC 4180 so it can be parsed by anything.
 *
 * **A BOM**, because Excel reads a UTF-8 CSV as the local 8-bit codepage without one, and every
 * "Dinonaktifkan — Sari Wulandari" arrives mojibaked.
 *
 * **A `sep=,` line**, because Excel does not assume the comma. It splits on the *operating
 * system's* list separator, which on an Indonesian or most European locales is `;` — so a
 * comma-separated file opens with every row crushed into column A, which is exactly what it did
 * before this line existed. `sep=` is an Excel convention rather than part of any CSV standard,
 * and it is the deliberate trade here: a strict RFC-4180 reader sees one junk row at the top,
 * and the auditor who double-clicks the file sees columns. This export is written to be read by
 * a person, so the person wins.
 *
 * **The object URL is revoked on a later task, not on this one.** `click()` only *schedules* the
 * download, and a same-tick revoke races it — Chrome happens to survive it, other engines do not,
 * and the failure mode is a file that silently never arrives. Not revoking at all is the other
 * end: the blob stays pinned for the life of the document. So the release is deferred by a timer.
 */
const REVOKE_DELAY_MS = 1000

/** Tells Excel which delimiter the file actually uses, instead of letting the locale guess. */
export const EXCEL_SEPARATOR_HINT = 'sep=,'

export function downloadCsv(filename: string, content: string): void {
  // The BOM is written as an escape, not as the character itself: a literal U+FEFF is invisible
  // in an editor and in a diff, so the one byte it represents could be dropped by an errant
  // autofix and nobody would see it go.
  const blob = new Blob([`\uFEFF${EXCEL_SEPARATOR_HINT}\r\n${content}`], {
    type: 'text/csv;charset=utf-8',
  })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.append(link)
  link.click()
  link.remove()
  setTimeout(() => URL.revokeObjectURL(url), REVOKE_DELAY_MS)
}

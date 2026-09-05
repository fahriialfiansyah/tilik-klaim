import { afterEach, describe, expect, test, vi } from 'vitest'

import {
  AUDIT_CSV_HEADER,
  auditCsvFilename,
  buildAuditCsv,
  downloadCsv,
  EXCEL_SEPARATOR_HINT,
} from '@/features/admin/users/csv'
import type { UserAuditEvent } from '@/features/admin/users/types'

const EVENT: UserAuditEvent = {
  event_id: 'uevt_1',
  event_kind: 'USER_ROLE_CHANGED',
  actor_user_id: 'usr_rina_hartati',
  actor_role: 'admin',
  target_user_id: 'usr_sari_wulandari',
  field: 'role',
  value_before: 'reviewer',
  value_after: 'senior_reviewer',
  occurred_at: '2026-09-04T02:15:00Z',
}

const NAMES: Readonly<Record<string, string>> = {
  usr_rina_hartati: 'Rina Hartati',
  usr_sari_wulandari: 'Sari Wulandari',
}

const nameFor = (userId: string) => NAMES[userId] ?? userId

function rows(csv: string): string[] {
  return csv.split('\r\n')
}

describe('the audit export', () => {
  test('leads with a header a person can read without the schema', () => {
    expect(rows(buildAuditCsv([EVENT], nameFor))[0]).toBe(
      AUDIT_CSV_HEADER.map((column) => `"${column}"`).join(','),
    )
  })

  test('writes working language, not stored values', () => {
    // `USER_ROLE_CHANGED` / `senior_reviewer` is the shape the database keeps. A governance
    // artefact that has to be decoded before it can be read is one nobody checks.
    const line = rows(buildAuditCsv([EVENT], nameFor))[1]
    expect(line).toContain('"Peran diubah"')
    expect(line).toContain('"Peninjau"')
    expect(line).toContain('"Peninjau Senior"')
    expect(line).toContain('"Sari Wulandari"')
    expect(line).toContain('"Rina Hartati"')
  })

  test('names the changed field in working language, not as a database column', () => {
    // `role` / `is_active` are Postgres column names. Two English identifiers in the middle of
    // an Indonesian sheet ask the reader to know the schema before they can read the record.
    expect(rows(buildAuditCsv([EVENT], nameFor))[1]).toContain('"Peran"')
    expect(
      rows(buildAuditCsv([{ ...EVENT, field: 'is_active' }], nameFor))[1],
    ).toContain('"Status aktif"')
  })

  test('an unrecognised field falls back to its raw name rather than vanishing', () => {
    expect(rows(buildAuditCsv([{ ...EVENT, field: 'something_new' }], nameFor))[1]).toContain(
      '"something_new"',
    )
  })

  test('keeps the raw event id so a row can be traced back', () => {
    expect(rows(buildAuditCsv([EVENT], nameFor))[1]).toContain('"uevt_1"')
  })

  test('stamps the time in WIB rather than in whatever zone the reader opens it in', () => {
    expect(rows(buildAuditCsv([EVENT], nameFor))[1]).toContain('"04 Sep 2026, 09.15 WIB"')
  })

  test('an active-flag change reads as Aktif and Nonaktif, and a null value as empty', () => {
    const line = rows(
      buildAuditCsv(
        [{ ...EVENT, field: 'is_active', value_before: 'true', value_after: 'false' }],
        nameFor,
      ),
    )[1]
    expect(line).toContain('"Aktif"')
    expect(line).toContain('"Nonaktif"')
    expect(rows(buildAuditCsv([{ ...EVENT, value_before: null }], nameFor))[1]).toContain('""')
  })

  test('quotes a comma and doubles an embedded quote rather than breaking the row', () => {
    const line = rows(
      buildAuditCsv([{ ...EVENT, event_id: 'a,b' }, { ...EVENT, event_id: 'say "hi"' }], nameFor),
    )
    expect(line[1]).toContain('"a,b"')
    expect(line[2]).toContain('"say ""hi"""')
    expect(line).toHaveLength(3)
  })

  test('a value that would run as a spreadsheet formula is defused, not deleted', () => {
    // `=HYPERLINK(...)` in a name field turns an audit export into an attack on whoever opens
    // it. The tab keeps the original text visible — no character of a governance record is
    // silently dropped on the way out.
    const attack = '=HYPERLINK("http://evil.example","klik")'
    const line = rows(buildAuditCsv([{ ...EVENT, event_id: attack }], nameFor))[1]
    // The guarded cell opens with a quote and a tab, so Excel sees text; the inner quotes are
    // doubled per RFC 4180, which is why this asserts the prefix rather than the whole string.
    expect(line).toContain('"\t=HYPERLINK(')
    expect(line).not.toContain('"=HYPERLINK')
  })

  test('an empty trail is a header and nothing else, never a blank file', () => {
    expect(rows(buildAuditCsv([], nameFor))).toHaveLength(1)
  })

  test('names the file for the Jakarta date, so a nightly export sorts correctly', () => {
    // 17:30 UTC is already the next day in Jakarta; naming it from the host zone would file two
    // different days under one name.
    expect(auditCsvFilename(new Date('2026-09-05T17:30:00Z'))).toBe(
      'riwayat-pengguna-2026-09-06.csv',
    )
  })
})

describe('handing the file to the browser', () => {
  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  function stubObjectUrl() {
    const revoke = vi.fn()
    vi.stubGlobal('URL', {
      ...URL,
      createObjectURL: vi.fn(() => 'blob:stub'),
      revokeObjectURL: revoke,
    })
    return revoke
  }

  test('offers the file under the name it was given and leaves no anchor behind', () => {
    stubObjectUrl()
    const click = vi
      .spyOn(HTMLAnchorElement.prototype, 'click')
      .mockImplementation(function (this: HTMLAnchorElement) {
        // Captured mid-click: the anchor is removed straight after, so asserting afterwards
        // would only ever see an empty document.
        expect(this.download).toBe('riwayat.csv')
        expect(this.href).toBe('blob:stub')
        expect(this.isConnected).toBe(true)
      })

    downloadCsv('riwayat.csv', 'a,b')

    expect(click).toHaveBeenCalledOnce()
    expect(document.querySelectorAll('a[download]')).toHaveLength(0)
  })

  test('releases the blob later, never in the tick that started the download', () => {
    // `click()` only schedules the download; revoking in the same tick races it, and the failure
    // is a file that silently never arrives. Not revoking at all pins the blob for the life of
    // the document — so this asserts both halves.
    vi.useFakeTimers()
    const revoke = stubObjectUrl()
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})

    downloadCsv('riwayat.csv', 'a,b')
    expect(revoke).not.toHaveBeenCalled()

    vi.runAllTimers()
    expect(revoke).toHaveBeenCalledWith('blob:stub')
  })

  test('leads the file with a BOM so Excel reads it as UTF-8', async () => {
    // Without it every "Dinonaktifkan — Sari Wulandari" arrives mojibaked.
    const create = vi.fn((_blob: Blob) => 'blob:stub')
    vi.stubGlobal('URL', { ...URL, createObjectURL: create, revokeObjectURL: vi.fn() })
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})

    downloadCsv('riwayat.csv', 'Sari')

    const blob = create.mock.calls[0][0] as unknown as Blob
    expect(blob.type).toBe('text/csv;charset=utf-8')
    // Read as bytes, not as text: `Blob.text()` runs a UTF-8 decode, and that decode strips the
    // very BOM this test exists to find. Asserting through it would pass with no BOM at all.
    const bytes = new Uint8Array(await blob.arrayBuffer())
    expect([...bytes.slice(0, 3)]).toEqual([0xef, 0xbb, 0xbf])
  })

  test('tells Excel the delimiter instead of letting the locale guess it', async () => {
    // Without this line Excel splits on the OS list separator — `;` on an Indonesian locale —
    // and the whole file lands in column A. That is not hypothetical: it is what happened.
    const create = vi.fn((_blob: Blob) => 'blob:stub')
    vi.stubGlobal('URL', { ...URL, createObjectURL: create, revokeObjectURL: vi.fn() })
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})

    downloadCsv('riwayat.csv', 'a,b')

    const text = await (create.mock.calls[0][0] as unknown as Blob).text()
    expect(text.split('\r\n')[0]).toBe(EXCEL_SEPARATOR_HINT)
    expect(text.endsWith('a,b')).toBe(true)
  })

  test('keeps the built content itself free of the Excel hint', () => {
    // `buildAuditCsv` stays plain RFC 4180 — the accommodation belongs to the download, so
    // anything that consumes the builder directly is unaffected by it.
    expect(buildAuditCsv([EVENT], nameFor)).not.toContain(EXCEL_SEPARATOR_HINT)
  })
})

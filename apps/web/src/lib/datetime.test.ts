import { describe, expect, test } from 'vitest'

import { ZONE_LABEL, formatDate, formatDateTime, formatTime, parseStamp } from '@/lib/datetime'

// 02:15 UTC on 4 September is 09.15 on 4 September in Jakarta.
const MORNING = '2026-09-04T02:15:00Z'
// 17:30 UTC on 5 September is already 00.30 on *6* September in Jakarta — the case that makes
// an unpinned formatter print the wrong day, not merely the wrong hour.
const LATE = '2026-09-05T17:30:00Z'

describe('the app clock', () => {
  test('reads in Jakarta regardless of the machine it runs on', () => {
    // This suite runs with TZ forced to a zone that is not Jakarta (see vitest.config), so a
    // formatter that had inherited the host would fail here rather than only in Singapore.
    expect(formatDateTime(MORNING)).toBe('04 Sep 2026, 09.15 WIB')
  })

  test('rolls the date over on Jakarta midnight, not the host machine s', () => {
    expect(formatDate(LATE)).toBe('06 Sep 2026')
  })

  test('says which zone it means when a stamp is read on its own', () => {
    expect(formatDateTime(MORNING)).toMatch(/WIB$/)
    expect(ZONE_LABEL).toBe('WIB')
  })

  test('stays quiet about the zone under a date that already established the day', () => {
    // A swimlane axis repeating "WIB" on every tick is noise, not precision.
    expect(formatTime(MORNING)).toBe('09.15')
  })

  test('renders an em dash rather than the words Invalid Date', () => {
    for (const bad of ['', 'not-a-date', null, undefined]) {
      expect(formatDateTime(bad)).toBe('—')
      expect(formatDate(bad)).toBe('—')
      expect(formatTime(bad)).toBe('—')
    }
  })

  test('tells absent apart from malformed', () => {
    // Both render as a dash, but a caller that needs to say "belum pernah" instead has to be
    // able to ask the difference.
    expect(parseStamp(null)).toBeNull()
    expect(parseStamp('not-a-date')).toBeNull()
    expect(parseStamp(MORNING)).toBeInstanceOf(Date)
  })
})

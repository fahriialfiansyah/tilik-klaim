import { describe, expect, test } from 'vitest'

import FAVICON from './favicon.svg?raw'

/**
 * The favicon is the one asset nothing else in the app renders, so nothing else fails when it
 * breaks — the browser quietly falls back to its default globe and the tab looks *almost* right.
 *
 * That is exactly what happened: the first version explained itself in an XML comment that named
 * design tokens (`--t-inv`, `--logo-amb`). A double hyphen is illegal inside an XML comment, so
 * the whole file was unparseable, and every browser showed its own icon instead. No test failed,
 * the build succeeded, and the link tag was present and correct.
 */
describe('favicon', () => {
  test('is well-formed XML — a broken one fails silently, so assert it here', () => {
    const parsed = new DOMParser().parseFromString(FAVICON, 'image/svg+xml')
    const error = parsed.querySelector('parsererror')
    expect(error?.textContent ?? null).toBeNull()
    expect(parsed.documentElement.tagName).toBe('svg')
  })

  test('carries no XML comment, because token names would break it again', () => {
    expect(FAVICON).not.toMatch(/<!--/)
  })

  test('paints every shape explicitly — browser chrome has no theme tokens to inherit', () => {
    // A `var(--…)` here resolves to nothing outside the page, and the icon renders blank.
    expect(FAVICON).not.toMatch(/var\(/)
    expect(FAVICON).toMatch(/#0b2530/)
    expect(FAVICON).toMatch(/#e8a33d/)
  })
})

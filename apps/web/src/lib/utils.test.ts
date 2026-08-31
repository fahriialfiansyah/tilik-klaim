import { describe, expect, test } from 'vitest'

import { cn } from '@/lib/utils'

describe('cn', () => {
  test('a size utility never displaces a text colour', () => {
    // Regression. tailwind-merge classified `text-body-lg` as a colour because it only knows
    // Tailwind's stock type scale, so it dropped `text-brand-on` as a conflicting colour and
    // every Button rendered near-black text on dark teal at 2.5:1.
    const merged = cn('bg-brand text-brand-on', 'h-11 text-body-lg')

    expect(merged).toContain('text-brand-on')
    expect(merged).toContain('text-body-lg')
  })

  test('two colours on the same property still collapse to the last one', () => {
    expect(cn('text-ink', 'text-brand')).toBe('text-brand')
  })

  test('two sizes still collapse to the last one', () => {
    expect(cn('text-small', 'text-lead')).toBe('text-lead')
  })
})

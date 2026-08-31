import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, test } from 'vitest'

import { ExpandableText } from '@/features/review/shared/components/ExpandableText'

const SHORT = 'Diperiksa manual terhadap berkas fisik.'
const LONG = 'Catatan panjang dari petugas peninjau.'.padEnd(38, ' ').repeat(20).trim()

describe('ExpandableText', () => {
  test('short text renders whole, with no control to clutter the line', () => {
    render(<ExpandableText text={SHORT} />)

    expect(screen.getByText(SHORT)).toBeVisible()
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  /**
   * It clamps rather than truncates: the whole text stays in the DOM and the control reveals it
   * in place. On an evidence screen, cutting a clinical note off at an ellipsis would leave the
   * reviewer no way to know what the elision removed.
   */
  test('long text keeps every character and offers to expand', async () => {
    render(<ExpandableText text={LONG} />)

    expect(screen.getByText(LONG)).toBeInTheDocument()
    const toggle = screen.getByRole('button', { name: /Tampilkan selengkapnya/ })
    expect(toggle).toHaveTextContent(String(LONG.length))

    await userEvent.click(toggle)
    expect(screen.getByRole('button', { name: 'Ringkaskan' })).toBeVisible()
  })

  test('the clamp is removed once expanded, and reapplied on collapse', async () => {
    render(<ExpandableText text={LONG} />)
    const body = screen.getByText(LONG)

    expect(body).toHaveClass('line-clamp-4')
    await userEvent.click(screen.getByRole('button'))
    expect(body).not.toHaveClass('line-clamp-4')
    await userEvent.click(screen.getByRole('button'))
    expect(body).toHaveClass('line-clamp-4')
  })
})

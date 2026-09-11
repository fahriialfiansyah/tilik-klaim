import { render } from '@testing-library/react'
import { describe, expect, test } from 'vitest'

import { useDocumentTitle } from '@/modules/document-title/useDocumentTitle'

function Page({ title }: { readonly title: string }) {
  useDocumentTitle(title)
  return null
}

describe('useDocumentTitle', () => {
  test('titles the tab after the page and the product', () => {
    render(<Page title="Audit & Evaluasi" />)

    expect(document.title).toBe('Audit & Evaluasi · TilikKlaim')
  })

  test('retitles when the page changes, so no route inherits the previous title', () => {
    const { rerender } = render(<Page title="Masuk" />)

    rerender(<Page title="Audit & Evaluasi" />)

    expect(document.title).toBe('Audit & Evaluasi · TilikKlaim')
  })
})

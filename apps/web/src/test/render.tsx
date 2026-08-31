import { render, type RenderResult } from '@testing-library/react'
import type { ReactElement } from 'react'
import { MemoryRouter } from 'react-router-dom'

/** Every component under test sits inside a router; none of them work without one. */
export function renderWithRouter(ui: ReactElement, route = '/'): RenderResult {
  return render(<MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter>)
}

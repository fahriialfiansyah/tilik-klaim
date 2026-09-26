import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, test } from 'vitest'

import { IssueTable } from '@/features/review/ingest/components/IssueTable'
import type { ValidationIssue } from '@/features/review/ingest/types'

const ISSUES: readonly ValidationIssue[] = [
  {
    code: 'BUNDLE_DANGLING_REFERENCE',
    resource_type: 'Procedure',
    resource_id: 'PROC-TIDAK-ADA',
    detail: 'Procedure/PROC-TIDAK-ADA is referenced but not present',
  },
]

describe('the issue table', () => {
  test('is titled for what it holds — problems with the file', () => {
    render(<IssueTable issues={ISSUES} />)

    expect(screen.getByText('Masalah pada berkas')).toBeVisible()
  })

  test('leads with the resource an operator has to open', () => {
    render(<IssueTable issues={ISSUES} />)

    expect(screen.getByText('PROC-TIDAK-ADA')).toBeVisible()
    expect(screen.getByText(/rujukan menunjuk ke resource yang tidak ikut terkirim/i))
      .toBeVisible()
  })

  /**
   * The code and the service's English sentence are engineer-facing. They stay reachable for a
   * ticket, but a reviewer reads the explanation first.
   */
  test('folds the code and the service text away', async () => {
    render(<IssueTable issues={ISSUES} />)

    expect(screen.getByText('BUNDLE_DANGLING_REFERENCE')).not.toBeVisible()
    expect(screen.getByText(ISSUES[0].detail)).not.toBeVisible()

    await userEvent.click(screen.getByText('Detail teknis'))

    expect(screen.getByText('BUNDLE_DANGLING_REFERENCE')).toBeVisible()
    expect(screen.getByText(ISSUES[0].detail)).toBeVisible()
  })
})

import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, test, vi } from 'vitest'

import { TechnicalDetails } from '@/features/review/ingest/components/TechnicalDetails'

function grantClipboard() {
  const writeText = vi.fn().mockResolvedValue(undefined)
  Object.defineProperty(navigator, 'clipboard', { value: { writeText }, configurable: true })
  return writeText
}

afterEach(() => {
  Object.defineProperty(navigator, 'clipboard', { value: undefined, configurable: true })
  Object.defineProperty(document, 'execCommand', { value: undefined, configurable: true })
})

describe('technical details', () => {
  /**
   * The stable code and the service's own sentence are written for an engineer reading a log.
   * A reviewer gets the explanation; the machine text stays reachable but never leads.
   */
  test('keeps the code out of the reading surface until it is asked for', () => {
    // Act
    render(<TechnicalDetails code="BUNDLE_SCHEMA_INVALID" detail="Top level must be an object" />)

    // Assert
    expect(screen.getByText('Detail teknis')).toBeVisible()
    expect(screen.getByText('BUNDLE_SCHEMA_INVALID')).not.toBeVisible()
    expect(screen.getByText('Top level must be an object')).not.toBeVisible()
  })

  test('reveals both the code and the service text on request', async () => {
    // Arrange
    render(<TechnicalDetails code="BUNDLE_SCHEMA_INVALID" detail="Top level must be an object" />)

    // Act
    await userEvent.click(screen.getByText('Detail teknis'))

    // Assert
    expect(screen.getByText('BUNDLE_SCHEMA_INVALID')).toBeVisible()
    expect(screen.getByText('Top level must be an object')).toBeVisible()
  })

  test('copies the code and the service text together, ready for a ticket', async () => {
    // Arrange
    const writeText = grantClipboard()
    render(<TechnicalDetails code="BUNDLE_SCHEMA_INVALID" detail="Top level must be an object" />)
    await userEvent.click(screen.getByText('Detail teknis'))

    // Act
    await userEvent.click(screen.getByRole('button', { name: 'Salin' }))

    // Assert
    expect(writeText).toHaveBeenCalledWith('BUNDLE_SCHEMA_INVALID\nTop level must be an object')
    expect(await screen.findByRole('button', { name: 'Tersalin' })).toBeVisible()
  })

  /** Silence on a failed copy is what made the old button look broken. */
  test('says so when the copy did not happen', async () => {
    // Arrange
    Object.defineProperty(navigator, 'clipboard', { value: undefined, configurable: true })
    Object.defineProperty(document, 'execCommand', { value: undefined, configurable: true })
    render(<TechnicalDetails code="BUNDLE_SCHEMA_INVALID" detail="Top level must be an object" />)
    await userEvent.click(screen.getByText('Detail teknis'))

    // Act
    await userEvent.click(screen.getByRole('button', { name: 'Salin' }))

    // Assert
    expect(await screen.findByRole('button', { name: 'Gagal menyalin' })).toBeVisible()
  })

  test('renders nothing when there is no code and no detail to show', () => {
    // Act
    const { container } = render(<TechnicalDetails code="" detail="" />)

    // Assert
    expect(container).toBeEmptyDOMElement()
  })
})

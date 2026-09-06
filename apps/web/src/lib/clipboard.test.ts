import { afterEach, describe, expect, test, vi } from 'vitest'

import { copyText } from '@/lib/clipboard'

function setClipboard(value: unknown) {
  Object.defineProperty(navigator, 'clipboard', { value, configurable: true })
}

function setExecCommand(value: unknown) {
  Object.defineProperty(document, 'execCommand', { value, configurable: true })
}

afterEach(() => {
  setClipboard(undefined)
  setExecCommand(undefined)
})

describe('copyText', () => {
  test('uses the async clipboard API when the browser grants it', async () => {
    // Arrange
    const writeText = vi.fn().mockResolvedValue(undefined)
    setClipboard({ writeText })

    // Act
    const copied = await copyText('sha256:abc')

    // Assert
    expect(copied).toBe(true)
    expect(writeText).toHaveBeenCalledWith('sha256:abc')
  })

  /**
   * The demo is routinely opened over plain HTTP on a LAN address, where `navigator.clipboard`
   * does not exist at all. Every copy button on the app was dead there.
   */
  test('falls back to a selection copy when the clipboard API is missing', async () => {
    // Arrange
    setClipboard(undefined)
    const execCommand = vi.fn(() => true)
    setExecCommand(execCommand)

    // Act
    const copied = await copyText('sha256:abc')

    // Assert
    expect(copied).toBe(true)
    expect(execCommand).toHaveBeenCalledWith('copy')
  })

  test('falls back when the async write is refused', async () => {
    // Arrange
    setClipboard({ writeText: vi.fn().mockRejectedValue(new Error('denied')) })
    const execCommand = vi.fn(() => true)
    setExecCommand(execCommand)

    // Act
    const copied = await copyText('sha256:abc')

    // Assert
    expect(copied).toBe(true)
  })

  test('leaves no stray node behind after the fallback runs', async () => {
    // Arrange
    setClipboard(undefined)
    setExecCommand(vi.fn(() => true))

    // Act
    await copyText('sha256:abc')

    // Assert
    expect(document.querySelector('textarea')).toBeNull()
  })

  /** A caller that gets `false` must not report success — the operator has to select by hand. */
  test('reports false when neither path is available', async () => {
    // Arrange
    setClipboard(undefined)
    setExecCommand(undefined)

    // Act & Assert
    await expect(copyText('sha256:abc')).resolves.toBe(false)
  })

  test('reports false when the fallback command itself fails', async () => {
    // Arrange
    setClipboard(undefined)
    setExecCommand(vi.fn(() => false))

    // Act & Assert
    await expect(copyText('sha256:abc')).resolves.toBe(false)
  })

  test('refuses empty text rather than reporting a copy that carried nothing', async () => {
    // Arrange
    const writeText = vi.fn().mockResolvedValue(undefined)
    setClipboard({ writeText })

    // Act & Assert
    await expect(copyText('')).resolves.toBe(false)
    expect(writeText).not.toHaveBeenCalled()
  })
})

import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, test, vi } from 'vitest'

import { Composer } from '@/features/review/assistant/components/Composer'
import { MAX_QUESTION_CHARS, QUEUE_SCOPE } from '@/features/review/assistant/types'
import type { QueueCasesState } from '@/features/review/assistant/useQueueCases'
import { renderWithRouter } from '@/test/render'

const QUEUE: QueueCasesState = { status: 'ready', cases: [] }

function setup(isBusy = false) {
  const onAsk = vi.fn()
  const onStop = vi.fn()
  renderWithRouter(
    <Composer
      scope={QUEUE_SCOPE}
      queue={QUEUE}
      isBusy={isBusy}
      onScopeChange={vi.fn()}
      onAsk={onAsk}
      onStop={onStop}
    />,
  )
  return { onAsk, onStop, input: screen.getByRole('textbox', { name: 'Pertanyaan untuk Asisten Bukti' }) }
}

describe('the question input', () => {
  test('Enter sends the trimmed question and clears the input', async () => {
    const { onAsk, input } = setup()
    await userEvent.type(input, '  Ringkas kondisi antrean  {Enter}')
    expect(onAsk).toHaveBeenCalledWith('Ringkas kondisi antrean')
    expect(input).toHaveValue('')
  })

  test('Shift+Enter breaks the line instead of sending', async () => {
    const { onAsk, input } = setup()
    await userEvent.type(input, 'baris satu{Shift>}{Enter}{/Shift}baris dua')
    expect(onAsk).not.toHaveBeenCalled()
    expect(input).toHaveValue('baris satu\nbaris dua')
  })

  test('an empty question cannot be sent', async () => {
    const { onAsk, input } = setup()
    expect(screen.getByRole('button', { name: 'Kirim pertanyaan' })).toBeDisabled()
    await userEvent.type(input, '   {Enter}')
    expect(onAsk).not.toHaveBeenCalled()
  })

  test('a question over the limit is stopped here, with the reason in words', async () => {
    const { onAsk, input } = setup()
    await userEvent.click(input)
    await userEvent.paste('x'.repeat(MAX_QUESTION_CHARS + 1))
    expect(input).toHaveAttribute('aria-invalid', 'true')
    expect(screen.getByText(/Pertanyaan terlalu panjang/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Kirim pertanyaan' })).toBeDisabled()
    await userEvent.keyboard('{Enter}')
    expect(onAsk).not.toHaveBeenCalled()
  })

  test('while an answer is prepared, the send button becomes stop and Escape stops too', async () => {
    const { onStop, input } = setup(true)
    expect(screen.queryByRole('button', { name: 'Kirim pertanyaan' })).not.toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Hentikan' }))
    await userEvent.type(input, '{Escape}')
    expect(onStop).toHaveBeenCalledTimes(2)
  })

  test('the scope is always shown beside the input', () => {
    setup()
    expect(screen.getByRole('button', { name: 'Ubah cakupan: Seluruh antrean' })).toBeInTheDocument()
  })
})

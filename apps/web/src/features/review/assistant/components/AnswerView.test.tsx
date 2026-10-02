import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, test, vi } from 'vitest'

import { AnswerView, type AnswerActions } from '@/features/review/assistant/components/AnswerView'
import { newTurn, withAnswer, withFailure } from '@/features/review/assistant/conversation'
import { ANSWER, CASE_ID, REFUSAL, RESOURCE_CITATION } from '@/features/review/assistant/test-fixtures'
import { QUEUE_SCOPE } from '@/features/review/assistant/types'
import { DISPOSITION_ACTIONS } from '@/features/review/case-detail/types'
import { renderWithRouter } from '@/test/render'

import apiSource from '../api?raw'
import conversationSource from '../conversation?raw'
import storeSource from '../store?raw'
import askSource from '../useAskAssistant?raw'
import drawerSource from '../useSourceDrawer?raw'
import answerSource from './AnswerView?raw'
import cardsSource from './CaseCards?raw'
import citationsSource from './Citations?raw'
import composerSource from './Composer?raw'
import pickerSource from './ScopePicker?raw'
import turnSource from './TurnView?raw'

function actions(): AnswerActions {
  return { onOpenResource: vi.fn(), onFocusCase: vi.fn(), onAsk: vi.fn(), onRetry: vi.fn() }
}

function done(answer = ANSWER) {
  return withAnswer(newTurn('t1', answer.question, QUEUE_SCOPE), answer, false)
}

describe('an answer reads statements first, then what they cite', () => {
  test('every statement carries numbered citations that match the source list', () => {
    renderWithRouter(<AnswerView turn={done()} isLatest isBusy={false} modes={[]} actions={actions()} />)

    // The inline chip and its entry in the source list are one source: same name, same target.
    for (const link of screen.getAllByRole('link', { name: 'Sumber 1: Kasus case_c459a18…' })) {
      expect(link).toHaveAttribute('href', `/cases/${CASE_ID}`)
    }
    for (const link of screen.getAllByRole('link', { name: 'Sumber 2: Antrean Review' })) {
      expect(link).toHaveAttribute('href', '/')
    }
    const sources = screen.getByRole('list', { name: 'Sumber' })
    expect(within(sources).getAllByRole('listitem')).toHaveLength(3)
  })

  test('a cited resource opens in place rather than navigating', async () => {
    const handlers = actions()
    renderWithRouter(<AnswerView turn={done()} isLatest isBusy={false} modes={[]} actions={handlers} />)

    await userEvent.click(screen.getAllByRole('button', { name: 'Sumber 3: baris tagihan LN-P2' })[0])
    expect(handlers.onOpenResource).toHaveBeenCalledWith(RESOURCE_CITATION)
  })

  test('a case card narrows the scope or opens the case — nothing else', async () => {
    const handlers = actions()
    renderWithRouter(<AnswerView turn={done()} isLatest isBusy={false} modes={[]} actions={handlers} />)

    await userEvent.click(screen.getByRole('button', { name: 'Persempit cakupan ke kasus case_c459a18…' }))
    expect(handlers.onFocusCase).toHaveBeenCalledWith(CASE_ID)
    expect(screen.getByRole('link', { name: /Buka kasus/ })).toHaveAttribute('href', `/cases/${CASE_ID}`)
  })

  test('provenance comes after the uncertainty, and follow-ups exclude what was just asked', () => {
    renderWithRouter(<AnswerView turn={done()} isLatest isBusy={false} modes={[]} actions={actions()} />)

    const text = document.body.textContent ?? ''
    expect(text.indexOf('KETIDAKPASTIAN')).toBeLessThan(text.indexOf('CARA DISUSUN'))
    expect(screen.getByText(/Templat deterministik, tanpa model bahasa/)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Kasus mana yang perlu dibuka dulu/ })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Ringkas kondisi antrean/ })).toBeInTheDocument()
  })

  test('a rejected model answer says so in words and keeps the reason behind a disclosure', () => {
    const rejected = {
      ...ANSWER,
      validation_rejected: true,
      rejection_reason: "forbidden term 'palsu'",
    }
    renderWithRouter(
      <AnswerView turn={done(rejected)} isLatest isBusy={false} modes={[]} actions={actions()} />,
    )
    expect(screen.getByText(/tidak lolos pemeriksaan rujukan dan istilah/)).toBeInTheDocument()
    expect(screen.getByText('Detail teknis').closest('details')).not.toHaveAttribute('open')
  })
})

describe('asking again keeps the question\'s own scope', () => {
  test('"Tanya ulang" hands back the turn, not just its words', async () => {
    const handlers = actions()
    const turn = withAnswer(
      newTurn('t1', 'Mengapa kasus ini muncul?', { kind: 'CASE', case_id: CASE_ID }),
      { ...ANSWER, scope: { kind: 'CASE', case_id: CASE_ID } },
      false,
    )
    renderWithRouter(<AnswerView turn={turn} isLatest isBusy={false} modes={[]} actions={handlers} />)
    await userEvent.click(screen.getByRole('button', { name: 'Tanya ulang' }))
    expect(handlers.onRetry).toHaveBeenCalledWith(turn)
    expect(handlers.onAsk).not.toHaveBeenCalled()
  })

  test('asking again is not offered while another answer is being prepared', () => {
    renderWithRouter(<AnswerView turn={done()} isLatest={false} isBusy modes={[]} actions={actions()} />)
    expect(screen.getByRole('button', { name: 'Tanya ulang' })).toBeDisabled()
  })
})

describe('a refusal and a failure explain themselves in plain words', () => {
  test('a refusal names the boundary and offers questions it can answer', async () => {
    const handlers = actions()
    renderWithRouter(
      <AnswerView turn={done(REFUSAL)} isLatest isBusy={false} modes={[]} actions={handlers} />,
    )
    expect(screen.getByText('Di luar cakupan asisten')).toBeInTheDocument()
    expect(screen.queryByRole('list', { name: 'Sumber' })).not.toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: /Ringkas kondisi antrean/ }))
    expect(handlers.onAsk).toHaveBeenCalledWith('Ringkas kondisi antrean')
  })

  test('a failure leads with the reader-facing sentence; the code is folded away', () => {
    const failed = withFailure(newTurn('t1', 'q', QUEUE_SCOPE), {
      code: 'CASE_NOT_FOUND',
      detail: 'No case nope',
    })
    renderWithRouter(<AnswerView turn={failed} isLatest isBusy={false} modes={[]} actions={actions()} />)

    expect(screen.getByRole('alert')).toHaveTextContent('Kasus ini tidak lagi ada di antrean')
    expect(screen.getByText('CASE_NOT_FOUND').closest('details')).not.toHaveAttribute('open')
  })
})

describe('the assistant has no path to a decision (ADR-0007 § 7)', () => {
  const FEATURE_SOURCES: Record<string, string> = {
    'api.ts': apiSource,
    'conversation.ts': conversationSource,
    'store.ts': storeSource,
    'useAskAssistant.ts': askSource,
    'useSourceDrawer.ts': drawerSource,
    'components/AnswerView.tsx': answerSource,
    'components/CaseCards.tsx': cardsSource,
    'components/Citations.tsx': citationsSource,
    'components/Composer.tsx': composerSource,
    'components/ScopePicker.tsx': pickerSource,
    'components/TurnView.tsx': turnSource,
  }

  test('the feature imports nothing from the disposition store', () => {
    for (const [name, source] of Object.entries(FEATURE_SOURCES)) {
      expect(source, name).not.toMatch(/case-detail\/store/)
      expect(source, name).not.toMatch(/saveDisposition/)
    }
  })

  test('no control in an answer names a disposition action', () => {
    renderWithRouter(<AnswerView turn={done()} isLatest isBusy={false} modes={[]} actions={actions()} />)
    for (const action of DISPOSITION_ACTIONS) {
      expect(document.body.textContent).not.toContain(action)
    }
  })
})

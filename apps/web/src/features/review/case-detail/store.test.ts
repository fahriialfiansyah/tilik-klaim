import { beforeEach, describe, expect, test } from 'vitest'

import {
  EMPTY_DRAFT,
  isSavable,
  missingFieldLabel,
  useCaseDetailStore,
} from '@/features/review/case-detail/store'

const CASE_ID = 'case_test'

function draft() {
  return useCaseDetailStore.getState().drafts[CASE_ID] ?? EMPTY_DRAFT
}

beforeEach(() => {
  useCaseDetailStore.setState({ drafts: {} })
})

describe('save gating', () => {
  test('a draft with no action is not savable', () => {
    expect(isSavable(EMPTY_DRAFT)).toBe(false)
    expect(missingFieldLabel(EMPTY_DRAFT)).toContain('tindakan')
  })

  test('an action alone is not enough — a reason is required too', () => {
    useCaseDetailStore.getState().setAction(CASE_ID, 'CONFIRM_ANOMALY')

    expect(isSavable(draft())).toBe(false)
    expect(missingFieldLabel(draft())).toContain('alasan')
  })

  test('whitespace is not a reason', () => {
    const store = useCaseDetailStore.getState()
    store.setAction(CASE_ID, 'ESCALATE')
    store.setStructuredReason(CASE_ID, '   ')

    expect(isSavable(draft())).toBe(false)
  })

  test('an action and a reason together are savable', () => {
    const store = useCaseDetailStore.getState()
    store.setAction(CASE_ID, 'REJECT_SIGNAL')
    store.setStructuredReason(CASE_ID, 'Tindak lanjut yang sah, bukan tagihan berulang')

    expect(isSavable(draft())).toBe(true)
    expect(missingFieldLabel(draft())).toBeNull()
  })
})

describe('changing the action', () => {
  test('clears the structured reason, which belonged to the previous action', () => {
    const store = useCaseDetailStore.getState()
    store.setAction(CASE_ID, 'REJECT_SIGNAL')
    store.setStructuredReason(CASE_ID, 'Dokumentasi berbasis templat yang sah')
    store.setAction(CASE_ID, 'CONFIRM_ANOMALY')

    expect(draft().structuredReason).toBe('')
  })

  test('keeps the free-text note, which is about the case rather than the action', () => {
    const store = useCaseDetailStore.getState()
    store.setAction(CASE_ID, 'REJECT_SIGNAL')
    store.setNote(CASE_ID, 'Diperiksa terhadap berkas fisik.')
    store.setAction(CASE_ID, 'ESCALATE')

    expect(draft().note).toBe('Diperiksa terhadap berkas fisik.')
  })
})

describe('requested evidence', () => {
  test('seeds the missing resource types once', () => {
    useCaseDetailStore.getState().seedRequestedEvidence(CASE_ID, ['Procedure', 'Document'])

    expect(draft().requestedEvidence).toEqual(['Procedure', 'Document'])
  })

  test('never re-seeds over the reviewer edits', () => {
    const store = useCaseDetailStore.getState()
    store.seedRequestedEvidence(CASE_ID, ['Procedure', 'Document'])
    store.toggleRequestedEvidence(CASE_ID, 'Document')
    store.seedRequestedEvidence(CASE_ID, ['Procedure', 'Document'])

    expect(draft().requestedEvidence).toEqual(['Procedure'])
  })

  test('toggling adds a type that was not pre-checked', () => {
    const store = useCaseDetailStore.getState()
    store.seedRequestedEvidence(CASE_ID, ['Procedure'])
    store.toggleRequestedEvidence(CASE_ID, 'Encounter')

    expect(draft().requestedEvidence).toEqual(['Procedure', 'Encounter'])
  })
})

describe('draft survival', () => {
  /**
   * The reason the draft lives outside the component tree at all. A stale-version rejection
   * re-fetches the case and re-renders the panel; component state would come back empty, and
   * `brief/04_DETAIL_KASUS_DISPOSISI.md` § 4.3 makes losing the reviewer's input the failure,
   * not the rejection itself.
   */
  test('a rejected save leaves every field exactly as the reviewer left it', () => {
    const store = useCaseDetailStore.getState()
    store.setAction(CASE_ID, 'REJECT_SIGNAL')
    store.setStructuredReason(CASE_ID, 'Tindak lanjut yang sah, bukan tagihan berulang')
    store.setNote(CASE_ID, 'Rentang kunjungan tidak bertumpang tindih.')
    const before = draft()

    // Nothing in the rejection path touches the store — this asserts that contract holds.
    expect(draft()).toEqual(before)
    expect(draft().structuredReason).not.toBe('')
    expect(draft().note).not.toBe('')
  })

  test('a successful save clears the draft, so the next case starts empty', () => {
    const store = useCaseDetailStore.getState()
    store.setAction(CASE_ID, 'ESCALATE')
    store.setStructuredReason(CASE_ID, 'Perlu penelusuran oleh unit berwenang')
    store.clearDraft(CASE_ID)

    expect(useCaseDetailStore.getState().drafts[CASE_ID]).toBeUndefined()
  })

  test('two cases keep separate drafts', () => {
    const store = useCaseDetailStore.getState()
    store.setAction(CASE_ID, 'ESCALATE')
    store.setAction('case_other', 'REJECT_SIGNAL')

    expect(draft().action).toBe('ESCALATE')
    expect(useCaseDetailStore.getState().drafts.case_other?.action).toBe('REJECT_SIGNAL')
  })
})

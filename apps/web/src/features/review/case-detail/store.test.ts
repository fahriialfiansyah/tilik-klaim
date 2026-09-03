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

describe('workspace — one selection, one drawer', () => {
  const SOURCE = { resource_type: 'Encounter', resource_id: 'ENC-1', label: 'Encounter ENC-1' } as const
  const CANDIDATE = {
    candidate_case_id: null,
    candidate_claim_id: 'CLM-2',
    fields: [],
    overlap_start: null,
    overlap_end: null,
    similarity_components: {},
    template_caveat: null,
  } as const

  function workspace() {
    return useCaseDetailStore.getState().workspace
  }

  beforeEach(() => {
    useCaseDetailStore
      .getState()
      .openCase(CASE_ID, { reasonCode: 'LINE_WITHOUT_COMPLETED_PROCEDURE', lineId: 'LN-P2' })
  })

  /**
   * ADR-0004 § Decision 4: the two drawers become one discriminated union, so "both open" is
   * unrepresentable rather than merely unlikely. Playwright's `getByRole('dialog')` is strict —
   * two dialogs would already fail the a11y suite — but a type that cannot express the state
   * is a stronger guarantee than a test that notices it.
   */
  test('opening a comparison while a source is open leaves only the comparison', () => {
    const store = useCaseDetailStore.getState()
    store.openSource(SOURCE)
    store.openComparison(CANDIDATE)

    expect(workspace().drawer).toEqual({ kind: 'comparison', candidate: CANDIDATE })
  })

  test('opening a source while a comparison is open leaves only the source', () => {
    const store = useCaseDetailStore.getState()
    store.openComparison(CANDIDATE)
    store.openSource(SOURCE)

    expect(workspace().drawer).toEqual({ kind: 'source', reference: SOURCE })
  })

  test('closing returns the drawer to none', () => {
    const store = useCaseDetailStore.getState()
    store.openSource(SOURCE)
    store.closeDrawer()

    expect(workspace().drawer).toEqual({ kind: 'none' })
  })

  test('selecting a different reason closes a drawer opened from the previous one', () => {
    const store = useCaseDetailStore.getState()
    store.openComparison(CANDIDATE)
    store.selectReason('DUPLICATE_CLAIM_FINGERPRINT')

    expect(workspace().reasonCode).toBe('DUPLICATE_CLAIM_FINGERPRINT')
    expect(workspace().drawer).toEqual({ kind: 'none' })
  })

  test('selecting a line closes an open drawer', () => {
    const store = useCaseDetailStore.getState()
    store.openSource(SOURCE)
    store.selectLine('LN-P1')

    expect(workspace().lineId).toBe('LN-P1')
    expect(workspace().drawer).toEqual({ kind: 'none' })
  })

  test('toggling the open reason closed keeps the line selection', () => {
    useCaseDetailStore.getState().selectReason(null)

    expect(workspace().reasonCode).toBeNull()
    expect(workspace().lineId).toBe('LN-P2')
  })

  test('opening another case resets the selection and closes the drawer', () => {
    const store = useCaseDetailStore.getState()
    store.openSource(SOURCE)
    store.openCase('case_other', { reasonCode: 'NEAR_DUPLICATE_DOCUMENTATION', lineId: null })

    expect(workspace()).toEqual({
      caseId: 'case_other',
      reasonCode: 'NEAR_DUPLICATE_DOCUMENTATION',
      lineId: null,
      drawer: { kind: 'none' },
    })
  })

  /**
   * The draft survives a refused save (above); it must equally survive everything the reviewer
   * does while *reading*. Opening a source, comparing a pair, and moving between reasons are all
   * reading, and none of them may cost a half-written disposition.
   */
  test('no workspace action touches the disposition draft', () => {
    const store = useCaseDetailStore.getState()
    store.setAction(CASE_ID, 'REQUEST_EVIDENCE')
    store.setStructuredReason(CASE_ID, 'Berkas pendukung belum lengkap')
    store.setNote(CASE_ID, 'Setengah jalan.')
    const before = draft()

    store.openSource(SOURCE)
    store.openComparison(CANDIDATE)
    store.selectReason('DUPLICATE_CLAIM_FINGERPRINT')
    store.selectLine('LN-P1')
    store.closeDrawer()
    store.openCase(CASE_ID, { reasonCode: null, lineId: null })

    expect(draft()).toEqual(before)
  })
})

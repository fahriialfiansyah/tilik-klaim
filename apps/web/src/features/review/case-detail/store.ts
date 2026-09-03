import { create } from 'zustand'

import type {
  ComparisonCandidate,
  DispositionAction,
  EvidenceRef,
  ResourceType,
} from '@/features/review/case-detail/types'

/** What the reviewer has typed and chosen, before it becomes a permanent record. */
export type DispositionDraft = {
  readonly action: DispositionAction | null
  readonly structuredReason: string
  readonly note: string
  readonly requestedEvidence: readonly ResourceType[]
  /**
   * Whether the missing-resource list has already been pre-checked once.
   *
   * "Minta bukti tambahan" ticks the resources the bundle lacks, and the reviewer may then add
   * or remove. Re-seeding on any later render would silently undo those edits, so the seeding
   * happens exactly once per case and this records that it did.
   */
  readonly evidenceSeeded: boolean
}

export const EMPTY_DRAFT: DispositionDraft = {
  action: null,
  structuredReason: '',
  note: '',
  requestedEvidence: [],
  evidenceSeeded: false,
}

/**
 * Which side panel is open, if any.
 *
 * One union rather than two booleans, so that "source and comparison both open" is a state the
 * type cannot express (ADR-0004 § Decision 4). Playwright's strict `getByRole('dialog')` would
 * catch two dialogs at runtime; making it unrepresentable is the stronger guarantee.
 */
export type DrawerState =
  | { readonly kind: 'none' }
  | { readonly kind: 'source'; readonly reference: EvidenceRef }
  | { readonly kind: 'comparison'; readonly candidate: ComparisonCandidate }

/** What the reviewer is looking at. Ephemeral — reset whenever a different case opens. */
export type Workspace = {
  readonly caseId: string | null
  readonly reasonCode: string | null
  readonly lineId: string | null
  readonly drawer: DrawerState
}

export type WorkspaceSeed = Pick<Workspace, 'reasonCode' | 'lineId'>

const CLOSED: DrawerState = { kind: 'none' }

export const EMPTY_WORKSPACE: Workspace = {
  caseId: null,
  reasonCode: null,
  lineId: null,
  drawer: CLOSED,
}

type CaseDetailStore = {
  readonly drafts: Readonly<Record<string, DispositionDraft>>
  readonly workspace: Workspace
  readonly openCase: (caseId: string, seed: WorkspaceSeed) => void
  readonly selectReason: (reasonCode: string | null) => void
  readonly selectLine: (lineId: string) => void
  readonly openSource: (reference: EvidenceRef) => void
  readonly openComparison: (candidate: ComparisonCandidate) => void
  readonly closeDrawer: () => void
  readonly setAction: (caseId: string, action: DispositionAction) => void
  readonly setStructuredReason: (caseId: string, reason: string) => void
  readonly setNote: (caseId: string, note: string) => void
  readonly seedRequestedEvidence: (caseId: string, types: readonly ResourceType[]) => void
  readonly toggleRequestedEvidence: (caseId: string, type: ResourceType) => void
  readonly clearDraft: (caseId: string) => void
}

function update(
  drafts: Readonly<Record<string, DispositionDraft>>,
  caseId: string,
  change: Partial<DispositionDraft>,
): Record<string, DispositionDraft> {
  const current = drafts[caseId] ?? EMPTY_DRAFT
  return { ...drafts, [caseId]: { ...current, ...change } }
}

/**
 * The reviewer's unsaved decision, held per case.
 *
 * It lives outside the component tree for one reason, and it is the reason the whole screen
 * exists: **a refused save must not cost the reviewer their input.** A stale-version rejection
 * re-fetches the case, which re-renders the panel; if the draft were component state it would
 * be reconstructed empty, and the person who just lost two minutes of reading would be told to
 * type it again. `brief/04_DETAIL_KASUS_DISPOSISI.md` § 4.3 and § 4.4 both turn on this.
 *
 * Server data is deliberately absent here — only the reviewer's own choices are client state.
 */
export const useCaseDetailStore = create<CaseDetailStore>((set) => ({
  drafts: {},
  workspace: EMPTY_WORKSPACE,

  // ---- workspace: selection and the one drawer -------------------------------------------
  //
  // Every action below returns a new `workspace` object and leaves `drafts` untouched by
  // construction — a reviewer reading a source or comparing a pair is not editing a decision,
  // and nothing here may cost them a half-written one.

  openCase: (caseId, seed) =>
    set(() => ({ workspace: { caseId, ...seed, drawer: CLOSED } })),

  // Changing what is selected closes whatever the previous selection opened: a comparison
  // drawer showing reason A's pair while reason B is selected would be a synchronised
  // workspace in name only.
  selectReason: (reasonCode) =>
    set((current) => ({ workspace: { ...current.workspace, reasonCode, drawer: CLOSED } })),

  selectLine: (lineId) =>
    set((current) => ({ workspace: { ...current.workspace, lineId, drawer: CLOSED } })),

  openSource: (reference) =>
    set((current) => ({
      workspace: { ...current.workspace, drawer: { kind: 'source', reference } },
    })),

  openComparison: (candidate) =>
    set((current) => ({
      workspace: { ...current.workspace, drawer: { kind: 'comparison', candidate } },
    })),

  closeDrawer: () =>
    set((current) => ({ workspace: { ...current.workspace, drawer: CLOSED } })),

  // ---- drafts: the reviewer's unsaved decision --------------------------------------------

  setAction: (caseId, action) =>
    set((current) => ({
      // A structured reason belongs to one action; carrying it across would submit a reason
      // that is not in the chosen action's list. The free-text note survives, because it is
      // the reviewer's own words about the case rather than about the action.
      drafts: update(current.drafts, caseId, {
        action,
        structuredReason: '',
        evidenceSeeded: false,
      }),
    })),

  setStructuredReason: (caseId, structuredReason) =>
    set((current) => ({ drafts: update(current.drafts, caseId, { structuredReason }) })),

  setNote: (caseId, note) =>
    set((current) => ({ drafts: update(current.drafts, caseId, { note }) })),

  seedRequestedEvidence: (caseId, types) =>
    set((current) => {
      const draft = current.drafts[caseId] ?? EMPTY_DRAFT
      if (draft.evidenceSeeded) {
        return { drafts: current.drafts }
      }
      return {
        drafts: update(current.drafts, caseId, {
          requestedEvidence: [...types],
          evidenceSeeded: true,
        }),
      }
    }),

  toggleRequestedEvidence: (caseId, type) =>
    set((current) => {
      const draft = current.drafts[caseId] ?? EMPTY_DRAFT
      const next = draft.requestedEvidence.includes(type)
        ? draft.requestedEvidence.filter((entry) => entry !== type)
        : [...draft.requestedEvidence, type]
      return { drafts: update(current.drafts, caseId, { requestedEvidence: next }) }
    }),

  clearDraft: (caseId) =>
    set((current) => {
      const { [caseId]: _saved, ...rest } = current.drafts
      return { drafts: rest }
    }),
}))

/** A decision is savable only once an action **and** a reason are both present. */
export function isSavable(draft: DispositionDraft): boolean {
  return draft.action !== null && draft.structuredReason.trim().length > 0
}

/** Which field is still missing, so the disabled button says why rather than just sitting there. */
export function missingFieldLabel(draft: DispositionDraft): string | null {
  if (draft.action === null) {
    return 'Pilih satu tindakan terlebih dahulu.'
  }
  if (draft.structuredReason.trim().length === 0) {
    return 'Pilih alasan terstruktur. Tidak ada disposisi tanpa alasan.'
  }
  return null
}

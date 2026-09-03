import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, test, vi } from 'vitest'

import { BriefingView } from '@/features/review/case-briefing/components/BriefingView'
import { IDLE_BRIEFING, fromBriefing, type BriefingState } from '@/features/review/case-briefing/events'
import type { CaseBriefing } from '@/features/review/case-briefing/types'
import { ACTION_LABELS } from '@/features/review/case-detail/labels'
import { PHANTOM_REASON, SOURCES } from '@/features/review/case-detail/test-fixtures'
import { renderWithRouter } from '@/test/render'

import apiSource from '../api?raw'
import eventsSource from '../events?raw'
import hookSource from '../useCaseBriefing?raw'
import panelSource from './BriefingPanel?raw'
import progressSource from './BriefingProgress?raw'
import viewSource from './BriefingView?raw'

const FEATURE_SOURCES: Record<string, string> = {
  'api.ts': apiSource,
  'events.ts': eventsSource,
  'useCaseBriefing.ts': hookSource,
  'components/BriefingPanel.tsx': panelSource,
  'components/BriefingProgress.tsx': progressSource,
  'components/BriefingView.tsx': viewSource,
}

const BRIEFING: CaseBriefing = {
  case_id: 'case_1',
  case_version: 1,
  observations: [
    {
      statement: 'Baris tagihan yang dirujuk tidak punya catatan tindakan yang dapat dibuka.',
      kind: 'EVIDENCE_GAP',
      source_refs: PHANTOM_REASON.evidence,
      reason_code: PHANTOM_REASON.code,
      confidence: 'STATED',
    },
  ],
  open_questions: [
    {
      question: 'Apakah catatan tindakan tersedia di sistem lain?',
      why_it_matters: 'Membedakan bukti yang tidak ada dari yang tidak ikut terkirim.',
      source_refs: PHANTOM_REASON.evidence,
    },
  ],
  uncertainty_note: 'Disusun hanya dari bukti yang ikut terkirim.',
  generated_by: 'TEMPLATE',
  model_id: null,
  prompt_version: 'template-1',
  validation_rejected: false,
  rejection_reason: null,
  tool_calls: [],
  versions: { schema_version: '0.1.0', ruleset_version: '0.1.0', engine_version: '0.1.0', dataset_version: 'unset' },
}

function renderView(state: BriefingState, isOpen = true) {
  const onStart = vi.fn()
  const onOpenSource = vi.fn()
  renderWithRouter(
    <BriefingView
      state={state}
      isOpen={isOpen}
      onToggle={vi.fn()}
      onStart={onStart}
      sources={SOURCES}
      onOpenSource={onOpenSource}
    />,
  )
  return { onStart, onOpenSource }
}

describe('the briefing panel is non-authoritative and on demand', () => {
  test('collapsed: only the heading and the disclaimer are rendered, nothing is fetched', () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch')
    renderView(IDLE_BRIEFING, false)

    expect(screen.getByRole('button', { name: /Ringkasan bukti/ })).toHaveAttribute('aria-expanded', 'false')
    expect(screen.getByText(/Tidak mengubah pita, status, atau keputusan/)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Susun ringkasan' })).not.toBeInTheDocument()
    expect(fetchSpy).not.toHaveBeenCalled()
    fetchSpy.mockRestore()
  })

  test('open and idle: the reviewer must ask for it', async () => {
    const { onStart } = renderView(IDLE_BRIEFING)
    await userEvent.click(screen.getByRole('button', { name: 'Susun ringkasan' }))
    expect(onStart).toHaveBeenCalledTimes(1)
  })

  test('exposes no control that names a disposition action', () => {
    renderView(fromBriefing(BRIEFING, false))
    for (const label of Object.values(ACTION_LABELS)) {
      expect(screen.queryByRole('button', { name: new RegExp(label) })).not.toBeInTheDocument()
    }
    expect(screen.queryByRole('radio')).not.toBeInTheDocument()
    expect(screen.queryByRole('checkbox')).not.toBeInTheDocument()
  })

  test('every observation reference opens through the source index', async () => {
    const { onOpenSource } = renderView(fromBriefing(BRIEFING, false))
    await userEvent.click(screen.getAllByRole('button', { name: /Kunjungan ENC-PH-1/ })[0])
    expect(onOpenSource).toHaveBeenCalledWith(expect.objectContaining({ resource_id: 'ENC-PH-1' }))
  })

  test('states its provenance after the content, and says when a model was refused', () => {
    renderView(fromBriefing({ ...BRIEFING, validation_rejected: true, rejection_reason: 'forbidden term: fraud' }, false))
    const text = document.body.textContent ?? ''
    expect(text.indexOf('PENGAMATAN')).toBeLessThan(text.indexOf('CARA DISUSUN'))
    expect(screen.getByText(/Templat deterministik/)).toBeInTheDocument()
    expect(screen.getByText(/ditolak validator/)).toBeInTheDocument()
  })

  test('a failed run says so without hiding the evidence above it', () => {
    renderView({ ...IDLE_BRIEFING, status: 'failed', error: 'Layanan tidak merespons.' })
    expect(screen.getByRole('alert')).toHaveTextContent(/tetap lengkap tanpa ringkasan ini/)
  })

  test('progress is announced politely and lists what was read, in order', () => {
    renderView({
      ...IDLE_BRIEFING,
      status: 'streaming',
      phase: 'READING',
      phaseDetail: 'get_timeline',
      toolCalls: [{ tool: 'list_reasons', arguments: {} }, { tool: 'get_timeline', arguments: {} }],
    })
    const status = screen.getByRole('status')
    expect(status).toHaveAttribute('aria-live', 'polite')
    expect(status).toHaveTextContent(/1\.\s*Membaca daftar alasan/)
    expect(status).toHaveTextContent(/2\.\s*Membaca linimasa episode/)
  })
})

describe('separation from the human decision', () => {
  /**
   * The panel must have no path to the draft. Asserted on the source, like the backend's
   * import-direction test: a future `useCaseDetailStore` import here is the failure.
   */
  test('the briefing feature imports nothing from the disposition store', () => {
    for (const [file, source] of Object.entries(FEATURE_SOURCES)) {
      expect(source, file).not.toMatch(/case-detail\/store/)
      expect(source, file).not.toMatch(/useCaseDetailStore/)
    }
  })

  test('no icon in the panel is a robot or a sparkle', () => {
    for (const file of ['components/BriefingView.tsx', 'components/BriefingPanel.tsx', 'components/BriefingProgress.tsx']) {
      expect(FEATURE_SOURCES[file], file).not.toMatch(/\b(Bot|Sparkles?|Brain|Wand)\b/)
    }
  })
})

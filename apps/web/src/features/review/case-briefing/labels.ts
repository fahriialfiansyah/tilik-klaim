import type { BriefingPhase, GeneratedBy, ObservationKind } from '@/features/review/case-briefing/types'

/**
 * Working-language copy for the briefing panel.
 *
 * The panel is named for what it is — a summary of evidence — and never for how it is made.
 * `01_product_decision.md` makes "readers describe it as an AI fraud detector / chatbot" a kill
 * criterion, so nothing here says agent, AI, or assistant, and the provenance line states the
 * mechanism only after the content.
 */

export const PANEL_TITLE = 'Ringkasan bukti'
export const PANEL_SUBTITLE =
  'Bukan penilaian. Tidak mengubah pita, status, atau keputusan. Alasan mentah di atas tetap menjadi acuan.'
export const START_LABEL = 'Susun ringkasan'
export const RESTART_LABEL = 'Susun ulang'

export const KIND_LABELS: Record<ObservationKind, string> = {
  EVIDENCE_GAP: 'Celah bukti',
  CORROBORATION: 'Dukungan',
  COUNTER_EVIDENCE: 'Bukti tandingan',
  COMPARISON: 'Perbandingan',
  TIMELINE: 'Urutan waktu',
  COMPLETENESS: 'Kelengkapan',
}

export const CONFIDENCE_LABELS = {
  STATED: 'tercatat langsung',
  INFERRED: 'disimpulkan',
} as const

export const PHASE_LABELS: Record<BriefingPhase, string> = {
  STARTED: 'Memulai',
  READING: 'Membaca',
  VALIDATING: 'Memeriksa rujukan dan istilah',
  DONE: 'Selesai',
}

export const GENERATED_BY_LABELS: Record<GeneratedBy, string> = {
  TEMPLATE: 'Templat deterministik, tanpa model bahasa',
  LLM: 'Model bahasa, tervalidasi',
}

/** The seven read-only tools, so the progress log reads as what was read, not as function names. */
export const TOOL_LABELS: Record<string, string> = {
  get_case_overview: 'Membaca ringkasan kasus',
  list_reasons: 'Membaca daftar alasan',
  get_evidence_path: 'Membaca jalur bukti',
  get_timeline: 'Membaca linimasa episode',
  get_counter_evidence: 'Membaca bukti tandingan',
  get_comparison_candidate: 'Membaca pasangan pembanding',
  get_source_resource: 'Membuka sumber daya',
}

export function toolLabel(tool: string): string {
  return TOOL_LABELS[tool] ?? tool
}

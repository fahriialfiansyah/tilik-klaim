import type { AssistantAnswer, CaseCard, Citation } from '@/features/review/assistant/types'

/** Wire-shaped fixtures for the assistant's unit tests — the shapes `dto/assistant.py` sends. */

export const CASE_ID = 'case_c459a18163fd48f29717db37dac71a2d'

export const QUEUE_CITATION: Citation = {
  kind: 'QUEUE',
  case_id: null,
  resource_type: null,
  resource_id: null,
  label: 'Antrean Review',
}

export const CASE_CITATION: Citation = {
  kind: 'CASE',
  case_id: CASE_ID,
  resource_type: null,
  resource_id: null,
  label: 'Kasus case_c459a18…',
}

export const RESOURCE_CITATION: Citation = {
  kind: 'RESOURCE',
  case_id: CASE_ID,
  resource_type: 'ClaimLine',
  resource_id: 'LN-P2',
  label: 'baris tagihan LN-P2',
}

export const CARD: CaseCard = {
  queue_position: 1,
  case: {
    reason_sentence: 'Baris tindakan ini tidak punya catatan tindakan yang selesai.',
    modes: ['PHANTOM_OR_NO_PROCEDURE_EVIDENCE'],
    case_id: CASE_ID,
    participant_token: 'PSN-1002',
    provider_token: 'PRV-01',
    evidence_completeness: {
      supported_lines: 1,
      total_lines: 2,
      missing_reference_count: 0,
      bundle_complete: true,
    },
    total_amount: '630000.00',
    currency: 'IDR',
    created_at: '2026-07-01T08:00:00Z',
    band: 'DETERMINISTIC_CONFLICT',
    state: 'SCREENED',
    case_version: 1,
  },
}

export const ANSWER: AssistantAnswer = {
  question: 'Kasus mana yang perlu dibuka dulu?',
  scope: { kind: 'QUEUE' },
  kind: 'ANSWER',
  intent: 'WHERE_TO_START',
  refusal_topic: null,
  notice: null,
  statements: [
    {
      text: 'Kasus teratas yang menunggu tinjauan adalah case_c459a18….',
      citations: [CASE_CITATION],
    },
    { text: 'Urutan ini milik antrean itu sendiri.', citations: [QUEUE_CITATION] },
    {
      text: 'Alasan terkuatnya: Baris tindakan ini tidak punya catatan tindakan yang selesai.',
      citations: [RESOURCE_CITATION, CASE_CITATION],
    },
  ],
  cases: [CARD],
  uncertainty_note: 'Jawaban ini hanya membaca antrean.',
  generated_by: 'TEMPLATE',
  model_id: null,
  prompt_version: 'assistant-template-1',
  validation_rejected: false,
  rejection_reason: null,
  tool_calls: [],
  versions: {
    schema_version: '0.1.0',
    ruleset_version: '0.1.0',
    engine_version: '0.1.0',
    dataset_version: 'unset',
  },
}

export const REFUSAL: AssistantAnswer = {
  ...ANSWER,
  question: 'Apakah kasus ini fraud?',
  kind: 'REFUSAL',
  intent: 'OUT_OF_SCOPE',
  refusal_topic: 'VERDICT',
  notice: 'Pertanyaan ini meminta kesimpulan tentang niat atau kesalahan pihak tertentu.',
  statements: [],
  cases: [],
}

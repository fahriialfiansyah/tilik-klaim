import type {
  CaseDetail,
  ComparisonCandidate,
  Reason,
  SourceResource,
} from '@/features/review/case-detail/types'

/**
 * A case detail shaped like the seeded phantom fixture.
 *
 * Values are copied from a real `GET /v1/cases/{id}` response rather than invented, so a test
 * that passes here is testing the shape the API actually sends. `apps/backend/tests/fixtures/api`
 * holds the committed originals.
 */

export const PHANTOM_REASON: Reason = {
  code: 'LINE_WITHOUT_COMPLETED_PROCEDURE',
  mode: 'PHANTOM_OR_NO_PROCEDURE_EVIDENCE',
  sentence: 'Baris tindakan ini tidak punya catatan tindakan yang selesai.',
  deterministic: true,
  expected_support: ['Procedure', 'Encounter'],
  evidence: [
    { resource_type: 'ClaimLine', resource_id: 'LN-P2', label: 'ClaimLine LN-P2' },
    { resource_type: 'Encounter', resource_id: 'ENC-PH-1', label: 'Encounter ENC-PH-1' },
  ],
  counter_evidence: [
    { resource_type: 'Encounter', resource_id: 'ENC-PH-1', label: 'Encounter ENC-PH-1' },
  ],
  counter_evidence_notes: [
    {
      note: 'Bundel ini hanya memuat bukti yang ikut terkirim. Tidak ditemukannya catatan di sini bukan bukti bahwa layanan tidak diberikan.',
      refs: [
        { resource_type: 'Encounter', resource_id: 'ENC-PH-1', label: 'Encounter ENC-PH-1' },
      ],
    },
  ],
  component_scores: { supporting_refs_found: 0 },
  ruleset_version: '0.1.0',
}

/** A repeat-billing reason that cites the other claim and no line of this one. */
export const REPEAT_REASON: Reason = {
  code: 'DUPLICATE_CLAIM_FINGERPRINT',
  mode: 'REPEAT_BILLING',
  sentence: 'Sidik klaim ini identik dengan klaim lain.',
  deterministic: true,
  expected_support: ['Claim'],
  evidence: [{ resource_type: 'Claim', resource_id: 'CLM-PRIOR', label: 'Claim CLM-PRIOR' }],
  counter_evidence: [],
  counter_evidence_notes: [],
  component_scores: { fingerprint_match: 1 },
  ruleset_version: '0.1.0',
}

export const SOURCES: readonly SourceResource[] = [
  {
    resource_type: 'Claim',
    resource_id: 'CLM-PRIOR',
    label: 'Claim CLM-PRIOR',
    availability: 'RELATED_BUNDLE',
    fields: [{ name: 'submitted_at', value: '2026-06-28T09:00:00Z' }],
  },
  {
    resource_type: 'ClaimLine',
    resource_id: 'LN-P2',
    label: 'ClaimLine LN-P2',
    availability: 'PRESENT',
    fields: [{ name: 'code', value: '88.71' }],
  },
  {
    resource_type: 'Encounter',
    resource_id: 'ENC-PH-1',
    label: 'Encounter ENC-PH-1',
    availability: 'PRESENT',
    fields: [{ name: 'status', value: 'finished' }],
  },
]

export const CLONE_COMPARISON: ComparisonCandidate = {
  candidate_case_id: null,
  candidate_claim_id: 'DOC-CL-1',
  fields: [
    {
      field_name: 'Jenis dokumen',
      left_value: 'clinical-note',
      right_value: 'clinical-note',
      matches: true,
    },
    { field_name: 'Panjang teks', left_value: '185', right_value: '184', matches: false },
  ],
  overlap_start: null,
  overlap_end: null,
  similarity_components: { text_similarity: 0.910053 },
  template_caveat:
    'Dokumentasi berbasis templat menghasilkan kemiripan tinggi tanpa ada yang disalin.',
}

export function makeCaseDetail(overrides: Partial<CaseDetail> = {}): CaseDetail {
  return {
    case_id: 'case_cf38e0ad34a242cdb63310bd7a3c4314',
    case_version: 1,
    state: 'SCREENED',
    participant_token: 'PSN-1002',
    provider_token: 'PRV-01',
    total_amount: '630000.00',
    currency: 'IDR',
    encounter_start: '2026-07-01T08:00:00Z',
    encounter_end: '2026-07-01T11:00:00Z',
    primary_reason: PHANTOM_REASON,
    reasons: [PHANTOM_REASON],
    band: {
      band: 'DETERMINISTIC_CONFLICT',
      basis: '1 alasan teramati; pita mengikuti alasan terkuat.',
      caps_applied: [],
    },
    lines: [
      {
        line_id: 'LN-P1',
        code: 'http://terminology.kemkes.go.id/CodeSystem/icd9cm 89.7',
        description: 'Layanan 89.7',
        quantity: '1',
        line_amount: '150000',
        service_at: '2026-07-01T09:00:00Z',
        support_state: 'SUPPORTED',
      },
      {
        line_id: 'LN-P2',
        code: 'http://terminology.kemkes.go.id/CodeSystem/icd9cm 88.71',
        description: 'Layanan 88.71',
        quantity: '1',
        line_amount: '480000',
        service_at: '2026-07-01T10:00:00Z',
        support_state: 'UNSUPPORTED',
      },
    ],
    timeline: [
      {
        occurred_at: '2026-07-01T08:00:00Z',
        kind: 'encounter',
        label: 'Kunjungan ENC-PH-1',
        resource: {
          resource_type: 'Encounter',
          resource_id: 'ENC-PH-1',
          label: 'Encounter ENC-PH-1',
        },
      },
    ],
    comparisons: [],
    evidence_completeness: {
      supported_lines: 1,
      total_lines: 2,
      missing_reference_count: 0,
      bundle_complete: true,
    },
    sources: SOURCES,
    suggested_action: null,
    versions: {
      schema_version: '0.1.0',
      ruleset_version: '0.1.0',
      engine_version: '0.1.0',
      dataset_version: 'unset',
    },
    ...overrides,
  }
}

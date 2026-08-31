import type { ValidationStatus } from '@/features/review/ingest/types'

/**
 * Working-language vocabulary for the ingest screen.
 *
 * The **completeness notes** are never composed here — they arrive from the backend already in
 * working language, so the ingest report and the case detail cannot disagree about what a
 * submission was missing.
 */

export const STATUS_LABELS: Record<ValidationStatus, string> = {
  VALID: 'Sah',
  VALID_WITH_NOTES: 'Sah dengan catatan',
  INVALID: 'Tidak sah',
}

/**
 * What each status means for what happens next.
 *
 * `VALID_WITH_NOTES` gets the longest explanation on purpose: it is the one a reader is most
 * likely to round to "invalid", and rounding it that way is the mistake the whole distinction
 * exists to prevent.
 */
export const STATUS_MEANINGS: Record<ValidationStatus, string> = {
  VALID: 'Bentuk berkas lolos pemeriksaan dan seluruh rujukan antar-sumber daya terselesaikan.',
  VALID_WITH_NOTES:
    'Bentuk berkas sah. Sebagian sumber daya pendukung memang tidak dikirim — bukan rusak, memang tidak ada. Catatan ini ikut tersimpan bersama kasus dan menurunkan tingkat keyakinan; ia tidak pernah menaikkan sinyal risiko.',
  INVALID:
    'Berkas tidak dapat disaring. Perbaiki sumber daya yang disebut di bawah lalu kirim ulang — tidak ada penyaringan sebagian.',
}

/**
 * Stable error codes translated into what went wrong and what to do about it.
 *
 * The API's own `detail` names the offending resource precisely and is kept beside this — but
 * it is written for an engineer reading a log. `docs/canonical/` requires the ingest report to
 * be *actionable*: the operator has to learn which resource to fix, not merely that something
 * somewhere is wrong.
 */
export const ISSUE_EXPLANATIONS: Record<string, string> = {
  BUNDLE_TOO_LARGE: 'Berkas melampaui batas ukuran yang diterima.',
  BUNDLE_UNSUPPORTED_CONTENT_TYPE: 'Tipe berkas tidak diterima; kirim satu berkas JSON.',
  BUNDLE_DEPTH_EXCEEDED: 'Struktur berkas bersarang terlalu dalam.',
  BUNDLE_MALFORMED_JSON: 'Isi berkas bukan JSON yang sah dan tidak dapat dibaca sama sekali.',
  BUNDLE_SCHEMA_INVALID:
    'Sebuah bidang tidak sesuai bentuk yang diharapkan — jenis datanya salah, atau bidang wajib tidak ada.',
  BUNDLE_UNKNOWN_RESOURCE_TYPE:
    'Jenis sumber daya ini di luar bagian skema yang didokumentasikan sistem.',
  BUNDLE_DANGLING_REFERENCE:
    'Sebuah rujukan menunjuk ke sumber daya yang tidak ikut terkirim. Rujukan yang tidak dapat diselesaikan adalah cacat integritas bukti, bukan sekadar bidang kosong.',
  BUNDLE_CIRCULAR_REFERENCE:
    'Sumber daya saling merujuk membentuk lingkaran, sehingga rantai buktinya tidak dapat ditelusuri.',
  BUNDLE_DUPLICATE_RESOURCE_ID:
    'Satu pengenal sumber daya dipakai lebih dari sekali, sehingga rujukan ke pengenal itu ambigu.',
  BUNDLE_TOTAL_MISMATCH:
    'Total klaim tidak sama dengan jumlah baris tagihannya.',
}

export function issueExplanation(code: string): string {
  return ISSUE_EXPLANATIONS[code] ?? 'Berkas ditolak oleh pemeriksaan bentuk.'
}

/** Resource-type names for the count summary, in the order a reader would look for them. */
export const COUNT_LABELS: Record<string, string> = {
  Claim: 'Klaim',
  ClaimLine: 'Baris tagihan',
  Encounter: 'Kunjungan',
  Condition: 'Diagnosis',
  Procedure: 'Tindakan',
  Medication: 'Obat',
  Diagnostic: 'Penunjang',
  Document: 'Catatan klinis',
  Account: 'Akun tagihan',
  ChargeItem: 'Item biaya',
  Invoice: 'Faktur',
}

export function countLabel(resourceType: string): string {
  return COUNT_LABELS[resourceType] ?? resourceType
}

/**
 * The order the count cards are shown in.
 *
 * The API returns them alphabetically, which puts `Account` and `ChargeItem` — billing plumbing
 * — ahead of the claim and its lines. A reader checking that a submission arrived intact looks
 * for the claim first and the invoice last.
 */
export const COUNT_ORDER: readonly string[] = [
  'Claim',
  'ClaimLine',
  'Encounter',
  'Condition',
  'Procedure',
  'Medication',
  'Diagnostic',
  'Document',
  'ChargeItem',
  'Invoice',
  'Account',
]

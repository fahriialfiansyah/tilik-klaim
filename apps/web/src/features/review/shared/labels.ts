import type { CaseState, PriorityBand, RiskMode } from '@/features/review/shared/types'

/**
 * Working-language labels for the wire enums.
 *
 * Reason *sentences* are never composed here — they come from the backend's reason catalog so
 * the queue and the case detail cannot disagree about why a case was raised. These maps cover
 * only the enum values, which have no sentence of their own.
 */

export const MODE_LABELS: Record<RiskMode, string> = {
  PHANTOM_OR_NO_PROCEDURE_EVIDENCE: 'Tagihan tanpa bukti',
  REPEAT_BILLING: 'Tagihan berulang',
  CLONED_DOCUMENTATION: 'Dokumentasi salinan',
  UNBUNDLING_FRAGMENTATION: 'Episode terpecah',
}

export const BAND_LABELS: Record<PriorityBand, string> = {
  DETERMINISTIC_CONFLICT: 'Konflik deterministik',
  HIGH_PRIORITY_SIGNAL: 'Sinyal prioritas tinggi',
  NEEDS_CONTEXT: 'Perlu konteks',
  // Never "bersih" and never "aman". The system observed nothing; that is not a clearance.
  NO_OBSERVED_RISK: 'Tidak ada risiko teramati',
}

/** Answers the queue's "why this band?" hover, in working language. */
export const BAND_BASIS: Record<PriorityBand, string> = {
  DETERMINISTIC_CONFLICT:
    'Sebuah aturan integritas dilanggar secara pasti. Merah menandai konflik itu — bukan kesalahan pihak mana pun.',
  HIGH_PRIORITY_SIGNAL: 'Perlu ditinjau. Baca sinyal pendukung dan penentangnya sebelum memutuskan.',
  NEEDS_CONTEXT:
    'Bukti belum cukup untuk menilai. Kemungkinan yang diperlukan adalah meminta kelengkapan, bukan menyimpulkan.',
  NO_OBSERVED_RISK:
    'Tidak ada detektor yang menyala pada versi mesin ini. Ini bukan pernyataan bahwa klaimnya bersih.',
}

export const STATE_LABELS: Record<CaseState, string> = {
  NEW: 'Baru',
  SCREENED: 'Tersaring',
  IN_REVIEW: 'Sedang ditinjau',
  EVIDENCE_REQUESTED: 'Menunggu bukti',
  DISMISSED: 'Sinyal ditolak',
  CONFIRMED_ANOMALY: 'Anomali dikonfirmasi',
  ESCALATED: 'Dieskalasi',
  INVALID_INPUT: 'Masukan tidak sah',
}

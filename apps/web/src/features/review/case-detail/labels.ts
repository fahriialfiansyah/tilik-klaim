import type {
  DispositionAction,
  Reason,
  ResourceType,
  SourceAvailability,
  SupportState,
} from '@/features/review/case-detail/types'

/**
 * Working-language labels for the case-detail screen, and the standard reasons a reviewer
 * picks from.
 *
 * The **reason sentences** are never composed here — they arrive from the backend's catalog, so
 * the queue and this screen cannot disagree about why a case was raised. What lives here is the
 * vocabulary the screen adds on top: action names, disposition reasons, resource names.
 */

export const ACTION_LABELS: Record<DispositionAction, string> = {
  REJECT_SIGNAL: 'Tolak sinyal',
  REQUEST_EVIDENCE: 'Minta bukti tambahan',
  CONFIRM_ANOMALY: 'Konfirmasi anomali',
  ESCALATE: 'Eskalasi',
}

/** What each action actually does, so a reviewer is never guessing at consequences. */
export const ACTION_MEANINGS: Record<DispositionAction, string> = {
  REJECT_SIGNAL:
    'Kasus ditutup dengan alasan. Peninjau berwenang masih dapat membukanya kembali.',
  REQUEST_EVIDENCE:
    'Kasus berpindah ke status menunggu bukti. Menunda dengan alasan yang tercatat adalah keputusan yang sah.',
  CONFIRM_ANOMALY:
    'Anda membenarkan adanya ketidaksesuaian yang perlu ditindaklanjuti. Ini bukan temuan fraud.',
  ESCALATE:
    'Kasus ditandai untuk penelusuran berwenang. Tidak ada sanksi, pembayaran, atau pemberitahuan otomatis.',
}

/**
 * The standard reasons offered per action.
 *
 * The system suggests; it never chooses. `brief/04_DETAIL_KASUS_DISPOSISI.md` § 7 is explicit
 * that nothing here may pre-select a reason or fill one in and save.
 */
export const STRUCTURED_REASONS: Record<DispositionAction, readonly string[]> = {
  REJECT_SIGNAL: [
    'Bukti pendukung ditemukan di luar bundel ini',
    'Tindak lanjut yang sah, bukan tagihan berulang',
    'Dokumentasi berbasis templat yang sah',
    'Layanan bertahap yang memang direncanakan',
    'Penandaan keliru-input sudah dikoreksi',
  ],
  REQUEST_EVIDENCE: [
    'Berkas pendukung belum lengkap',
    'Catatan tindakan belum terkirim',
    'Perlu penjelasan tertulis dari fasilitas',
    'Rujukan bukti tidak dapat diselesaikan',
  ],
  CONFIRM_ANOMALY: [
    'Baris tertagih tanpa bukti layanan yang selesai',
    'Klaim tumpang tindih pada episode yang sama',
    'Episode terpecah menjadi beberapa klaim',
    'Dokumentasi tersalin tanpa penjelasan yang wajar',
  ],
  ESCALATE: [
    'Perlu penelusuran oleh unit berwenang',
    'Pola berulang pada fasilitas ini',
    'Nilai dan dampak di luar kewenangan peninjau',
  ],
}

export const SUPPORT_LABELS: Record<SupportState, string> = {
  SUPPORTED: 'Didukung',
  PARTIALLY_SUPPORTED: 'Dukungan sebagian',
  UNSUPPORTED: 'Tidak didukung',
  // Not a softer "unsupported". The file was too thin to judge — that is a different finding.
  NOT_ASSESSABLE: 'Tidak dapat dinilai',
}

export const SUPPORT_MEANINGS: Record<SupportState, string> = {
  SUPPORTED: 'Bukti pendukung yang diharapkan ditemukan di bundel ini.',
  PARTIALLY_SUPPORTED: 'Sebagian bukti yang diharapkan ditemukan, sebagian belum.',
  UNSUPPORTED: 'Bukti yang diharapkan tidak ada, sementara berkasnya dinyatakan lengkap.',
  NOT_ASSESSABLE:
    'Berkasnya belum lengkap, sehingga baris ini belum dapat dinilai — bukan berarti buktinya tidak ada.',
}

export const RESOURCE_LABELS: Record<ResourceType, string> = {
  Claim: 'Klaim',
  ClaimLine: 'Baris tagihan',
  Encounter: 'Kunjungan',
  Condition: 'Diagnosis',
  Procedure: 'Tindakan',
  Medication: 'Obat',
  Diagnostic: 'Pemeriksaan penunjang',
  Document: 'Catatan klinis',
  Account: 'Akun tagihan',
  ChargeItem: 'Item biaya',
  Invoice: 'Faktur',
  Episode: 'Episode',
  Practitioner: 'Tenaga kesehatan',
}

export const AVAILABILITY_LABELS: Record<SourceAvailability, string> = {
  PRESENT: 'Ada di bundel ini',
  RELATED_BUNDLE: 'Milik bundel pembanding',
  NOT_STORED: 'Dirujuk lewat identitas',
  MISSING: 'Tidak dapat dibuka',
}

export const AVAILABILITY_MEANINGS: Record<SourceAvailability, string> = {
  PRESENT: 'Sumber daya ini dikirim bersama klaim dan ditampilkan apa adanya.',
  RELATED_BUNDLE:
    'Sumber daya ini berasal dari kiriman lain yang dibandingkan. Hanya bidang yang tidak mengungkap identitas peserta lain yang ditampilkan.',
  NOT_STORED:
    'Episode dan tenaga kesehatan dirujuk lewat identitas dan memang tidak disimpan sebagai sumber daya tersendiri. Ini bukan cacat.',
  MISSING:
    'Rujukan ini menunjuk ke sumber daya yang tidak dapat diselesaikan. Ini cacat integritas bukti, bukan tampilan kosong yang wajar.',
}

/** Field names inside a raw resource, so the source panel is readable without a schema. */
export const SOURCE_FIELD_LABELS: Record<string, string> = {
  account_id: 'Pengenal akun',
  authored_at: 'Ditulis',
  author_id: 'Penulis',
  care_type: 'Jenis perawatan',
  class_code: 'Kelas kunjungan',
  claim_id: 'Pengenal klaim',
  code: 'Kode',
  code_system: 'Sistem kode',
  currency: 'Mata uang',
  description: 'Keterangan',
  document_id: 'Pengenal dokumen',
  effective_at: 'Berlaku',
  encounter_id: 'Pengenal kunjungan',
  end_at: 'Selesai',
  episode_id: 'Pengenal episode',
  kind: 'Jenis',
  line_amount: 'Nominal baris',
  line_id: 'Pengenal baris',
  occurred_at: 'Waktu',
  onset_at: 'Awal keluhan',
  participant_id: 'Peserta (pseudonim)',
  performed_at: 'Dilakukan',
  performer_id: 'Pelaksana',
  location_id: 'Lokasi',
  issued_at: 'Diterbitkan',
  charge_item_id: 'Pengenal item biaya',
  condition_id: 'Pengenal diagnosis',
  diagnostic_id: 'Pengenal penunjang',
  invoice_id: 'Pengenal faktur',
  medication_id: 'Pengenal obat',
  procedure_id: 'Pengenal tindakan',
  provider_id: 'Fasilitas',
  quantity: 'Jumlah',
  recorded_at: 'Dicatat',
  result_at: 'Hasil',
  service_at: 'Waktu layanan',
  start_at: 'Mulai',
  status: 'Status',
  submitted_at: 'Dikirim',
  text: 'Isi catatan',
  text_digest: 'Sidik teks',
  text_hash: 'Sidik teks',
  text_length: 'Panjang teks',
  total_amount: 'Total',
  unit_price: 'Harga satuan',
  verification_status: 'Status verifikasi',
}

export function sourceFieldLabel(name: string): string {
  return SOURCE_FIELD_LABELS[name] ?? name
}

/** Component-score keys, which are rule internals and unreadable without a translation. */
export const COMPONENT_LABELS: Record<string, string> = {
  candidate_floor: 'Ambang kandidat',
  fingerprint_match: 'Kecocokan sidik klaim',
  hours_apart: 'Jarak waktu (jam)',
  reporting_threshold: 'Ambang pelaporan',
  shared_code_count: 'Kode layanan yang sama',
  supporting_refs_found: 'Rujukan pendukung ditemukan',
  text_similarity: 'Kemiripan teks',
}

export function componentLabel(name: string): string {
  return COMPONENT_LABELS[name] ?? name
}

/**
 * Every `event_kind` the API can write. Kept exhaustive on purpose — an unlabelled kind falls
 * through to the raw enum, and `OPENED` shipped that way for a while: the audit tab read
 * "OPENED" in the middle of an otherwise Indonesian history.
 */
export const AUDIT_KIND_LABELS: Record<string, string> = {
  CREATED: 'Kasus dibuat',
  SCREENED: 'Kasus disaring',
  RESCREENED: 'Kasus disaring ulang',
  OPENED: 'Kasus dibuka untuk ditinjau',
  DISPOSITION: 'Disposisi dicatat',
  SUPERSEDE: 'Koreksi disposisi',
}

export function auditKindLabel(kind: string): string {
  return AUDIT_KIND_LABELS[kind] ?? kind
}

export const ACTOR_LABELS: Record<string, string> = {
  reviewer: 'Petugas peninjau',
  senior_reviewer: 'Peninjau senior',
  auditor: 'Auditor',
  system: 'Sistem',
}

export function actorLabel(role: string): string {
  return ACTOR_LABELS[role] ?? role
}

export const STRENGTH_LABELS = ['lemah', 'sedang', 'kuat'] as const
export type Strength = 1 | 2 | 3

/**
 * How strongly the evidence supports one reason, on the three-step scale the card draws.
 *
 * Deterministic means a rule was violated for certain; a scored reason is a resemblance worth
 * looking at. Counter-evidence lowers either one, because an argument against a signal is part
 * of how strong that signal actually is — not a footnote under it.
 *
 * This mirrors the ordering the API applies (`order_by_strength`), so the meter never
 * contradicts the sequence the cards arrive in.
 */
export function reasonStrength(reason: Reason): Strength {
  const weakened = reason.counter_evidence_notes.length > 0
  if (reason.deterministic) {
    return weakened ? 2 : 3
  }
  return weakened ? 1 : 2
}

export function strengthLabel(reason: Reason): string {
  return STRENGTH_LABELS[reasonStrength(reason) - 1]
}

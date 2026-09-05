import type { BaselineId } from '@/features/review/evaluation/types'

/**
 * Working-language labels. Identifiers stay English; everything a reviewer reads is Indonesian.
 *
 * The metric names are deliberately spelled out rather than left as `P@K` or `PR-AUC`. This page
 * is read by the proposal team as well as by engineers, and an abbreviation nobody can expand is
 * a number nobody can defend.
 */

export const BASELINE_LABEL: Readonly<Record<BaselineId, string>> = {
  B0_RANDOM: 'Acak',
  B1_RULES_ONLY: 'Aturan saja',
  B2_STATISTICAL_ONLY: 'Statistik saja',
  HYBRID: 'TilikKlaim (hibrida)',
}

export const BASELINE_HINT: Readonly<Record<BaselineId, string>> = {
  B0_RANDOM: 'Urutan acak pada kapasitas review yang sama',
  B1_RULES_ONLY: 'Aturan struktural, sidik klaim, dan jendela waktu',
  B2_STATISTICAL_ONLY: 'Skor kemiripan dan anomali tanpa aturan deterministik',
  HYBRID: 'Aturan yang mempertahankan alasan, ditambah skor terkalibrasi',
}

export const METRIC_LABEL = {
  macro_f1: 'F1 makro',
  pr_auc: 'Luas kurva ketepatan-keterpanggilan',
  precision_at_k: 'Ketepatan pada kapasitas review',
  recall_at_k: 'Keterpanggilan pada kapasitas review',
  false_positives_per_100_clean: 'Positif palsu per 100 klaim bersih',
} as const

/** Shown wherever a value is absent from the artifact. Never a zero. */
export const NOT_MEASURED = 'Tidak terukur'

export const NOT_MEASURED_HINT =
  'Nilai ini tidak terdefinisi pada run tersebut, jadi tidak ditampilkan sebagai angka.'


/**
 * Indonesian renderings for the canonical limitations rows.
 *
 * `docs/canonical/06_evaluation_plan.md` states these rows in English and the artifact
 * `LIMITATIONS.md` carries them **verbatim**, because a canonical row paraphrased in an artifact
 * stops being quotable. This screen is read in Indonesian, so the page renders the translation
 * and the artifact keeps the original.
 *
 * The lookup falls back to the source string. A caveat the runner adds later shows up in
 * English rather than vanishing — a missing limitation is far worse than an untranslated one.
 */
export const LIMITATION_ID: Readonly<Record<string, string>> = {
  'Software correctly parses the chosen schema subset':
    'Perangkat lunak membaca subset skema yang dipilih dengan benar',
  'Detectors recover known injected patterns':
    'Detektor menemukan kembali pola yang sengaja disuntikkan',
  'Hybrid ranking may beat baselines on controlled cases':
    'Peringkat hibrida dapat mengungguli baseline pada kasus terkendali',
  'Evidence references and audit events are reproducible':
    'Rujukan bukti dan jejak audit dapat direproduksi',
  'Prototype latency and workflow can be measured':
    'Waktu proses dan alur kerja purwarupa dapat diukur',
  'Production compatibility with BPJS/E-Klaim/SATUSEHAT':
    'Kesesuaian produksi dengan BPJS / E-Klaim / SATUSEHAT',
  'Real-world JKN fraud accuracy or prevalence':
    'Akurasi atau prevalensi kecurangan JKN di dunia nyata',
  'National savings or causal impact': 'Penghematan nasional atau dampak kausal',
  'Clinical validity or legal findings': 'Keabsahan klinis atau temuan hukum',
  'Scale under national production load': 'Ketahanan pada beban produksi skala nasional',
}

export const MANDATORY_STATEMENT_ID =
  'Kumpulan data ini bersifat sintetik dan tidak menggambarkan prevalensi JKN maupun perilaku ' +
  'fasilitas kesehatan yang sebenarnya.'

export function toWorkingLanguage(line: string): string {
  return LIMITATION_ID[line] ?? line
}

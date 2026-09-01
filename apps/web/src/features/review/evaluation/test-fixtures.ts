import type { EvaluationResponse } from '@/features/review/evaluation/types'

/**
 * A response shaped exactly as `evaluation/runner` writes one, including the omissions.
 *
 * `B0_RANDOM` and `CLONED_DOCUMENTATION` are **absent** rather than zero-valued, which is what
 * the API does when a metric is undefined. Tests that only ever see a complete response would
 * never exercise the distinction the whole page is built around.
 */
export const EVALUATION_FIXTURE: EvaluationResponse = {
  run_id: 'run-20260901T000000Z',
  completed_at: '2026-09-01T00:00:00+00:00',
  data_class: 'synthetic',
  baselines: [
    {
      baseline: 'B1_RULES_ONLY',
      macro_f1: 0.651,
      pr_auc: 0.7122,
      precision_at_k: 0.9565,
      recall_at_k: 0.3667,
      false_positives_per_100_clean: 51.875,
    },
    {
      baseline: 'B2_STATISTICAL_ONLY',
      macro_f1: 0.2276,
      pr_auc: 0.673,
      precision_at_k: 0.7826,
      recall_at_k: 0.2833,
      false_positives_per_100_clean: 25,
    },
    {
      baseline: 'HYBRID',
      macro_f1: 0.651,
      pr_auc: 0.844,
      precision_at_k: 1,
      recall_at_k: 0.3833,
      false_positives_per_100_clean: 52.5,
    },
  ],
  per_mode: [
    {
      mode: 'PHANTOM_OR_NO_PROCEDURE_EVIDENCE',
      precision: 0.8,
      recall: 0.75,
      f1: 0.774,
      support: 12,
    },
    { mode: 'REPEAT_BILLING', precision: 0.9, recall: 0.6, f1: 0.72, support: 15 },
    {
      mode: 'UNBUNDLING_FRAGMENTATION',
      precision: 0.7,
      recall: 0.5,
      f1: 0.583,
      support: 11,
    },
  ],
  latency_p50_ms: 2,
  latency_p95_ms: 3,
  manifest: {
    dataset_hash: '1ff95898c696',
    generator_version: '0.1.0',
    split_manifest_hash: 'aa11',
    feature_version: '0.1.0',
    ruleset_version: '0.1.0',
    model_version: '0.1.0',
    threshold_logic: 'Kuantil distribusi skor validasi.',
    code_commit: 'abc123-dirty',
    environment_hash: 'bb22',
    artifact_hashes: { 'metrics.json': 'cc33' },
  },
  limitations: {
    demonstrates: ['Detectors recover known injected patterns'],
    does_not_demonstrate: [
      'Real-world JKN fraud accuracy or prevalence',
      'Measured on 228 held-out bundles, of which 168 carry no injection.',
    ],
    mandatory_statement:
      'This dataset is synthetic and does not represent JKN prevalence or real provider behavior.',
  },
  versions: {
    schema_version: '0.1.0',
    ruleset_version: '0.1.0',
    engine_version: '0.1.0',
    dataset_version: '1ff95898c696',
  },
}

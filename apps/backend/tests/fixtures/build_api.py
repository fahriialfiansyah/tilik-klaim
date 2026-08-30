"""Build one committed example response per endpoint.

These are the frontend's build target. Sprint 04's UI is developed against these files, so it
does not wait for a working backend — that parallelism is the whole point of freezing the
contract early (§ 20 *Initial backlog*).

Deterministic: fixed timestamps, no randomness. Regenerating is a no-op unless the contract
actually changed.
"""
from __future__ import annotations

import json
import pathlib
from datetime import UTC, datetime
from decimal import Decimal

from app.dto.bundles import (
    IngestBundleResponse,
    ResourceCount,
    ScreenResponse,
    ValidationStatus,
)
from app.dto.cases import (
    CaseDetailResponse,
    CaseQueueResponse,
    CaseSummary,
    ClaimLineView,
    ComparisonCandidate,
    ComparisonField,
    EvidenceCompleteness,
    QueueMetrics,
    TimelineEvent,
)
from app.dto.common import BandExplanation, EvidenceRefDto, PageInfo, ReasonDto, VersionStamp
from app.dto.dispositions import AuditEvent, AuditResponse, DispositionResponse
from app.dto.evaluations import (
    BaselineMetrics,
    EvaluationResponse,
    LimitationsCard,
    ModeMetrics,
    RunManifest,
)
from app.errors import ErrorCode, ErrorResponse, ValidationIssue
from tilik_domain.canonical import ResourceType
from tilik_domain.reasons import CaseState, DispositionAction, PriorityBand, ReasonCode, RiskMode
from tilik_domain.versioning import ENGINE_VERSION, RULESET_VERSION, SCHEMA_VERSION

OUT = pathlib.Path(__file__).parent / "api"
T0 = datetime(2026, 7, 2, 9, 0, tzinfo=UTC)

VERSIONS = VersionStamp(
    schema_version=SCHEMA_VERSION,
    ruleset_version=RULESET_VERSION,
    engine_version=ENGINE_VERSION,
    dataset_version="gold-0.1.0",
)

PHANTOM_REASON = ReasonDto(
    code=ReasonCode.LINE_WITHOUT_COMPLETED_PROCEDURE,
    mode=RiskMode.PHANTOM_OR_NO_PROCEDURE_EVIDENCE,
    sentence="Baris tindakan ini tidak punya catatan tindakan yang selesai.",
    deterministic=True,
    evidence=(
        EvidenceRefDto(
            resource_type=ResourceType.CLAIM_LINE,
            resource_id="LN-P2",
            label="Baris tagihan 88.71 — Rp480.000",
        ),
        EvidenceRefDto(
            resource_type=ResourceType.ENCOUNTER,
            resource_id="ENC-PH-1",
            label="Kunjungan rawat jalan 1 Juli 2026",
        ),
    ),
    counter_evidence=(),
    component_scores={"evidence_completeness": 0.5},
    ruleset_version=RULESET_VERSION,
)

COMPLETENESS = EvidenceCompleteness(
    supported_lines=1, total_lines=2, missing_reference_count=1, bundle_complete=True
)


def write(name: str, model) -> None:
    path = OUT / f"{name}.json"
    path.write_text(
        json.dumps(json.loads(model.model_dump_json()), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"  {name}")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("Building API fixtures:")

    write(
        "post_bundles",
        IngestBundleResponse(
            ingestion_id="ING-0001",
            status=ValidationStatus.VALID,
            input_hash="9f2c1b7e4a" + "0" * 54,
            resource_counts=(
                ResourceCount(resource_type="Claim", count=1),
                ResourceCount(resource_type="ClaimLine", count=2),
                ResourceCount(resource_type="Encounter", count=1),
                ResourceCount(resource_type="Procedure", count=1),
            ),
            issues=(),
            completeness_notes=(),
            is_screenable=True,
            existing_case_id=None,
            schema_version=SCHEMA_VERSION,
        ),
    )

    write(
        "post_bundles_invalid",
        IngestBundleResponse(
            ingestion_id="ING-0002",
            status=ValidationStatus.INVALID,
            input_hash="3b8d0a5c19" + "0" * 54,
            resource_counts=(ResourceCount(resource_type="Claim", count=1),),
            issues=(
                ValidationIssue(
                    code=ErrorCode.BUNDLE_DANGLING_REFERENCE,
                    resource_type="ClaimLine",
                    resource_id="LN-X1",
                    detail="Rujukan ke Procedure PROC-MISSING tidak ditemukan dalam bundel.",
                ),
            ),
            is_screenable=False,
            schema_version=SCHEMA_VERSION,
        ),
    )

    write(
        "post_screen",
        ScreenResponse(
            case_id="CASE-0001",
            case_version=1,
            state=str(CaseState.SCREENED),
            primary_reason=PHANTOM_REASON,
            reasons=(PHANTOM_REASON,),
            band=BandExplanation(
                band=PriorityBand.DETERMINISTIC_CONFLICT,
                basis="Sebuah aturan integritas berversi dilanggar secara pasti.",
                caps_applied=(),
            ),
            versions=VERSIONS,
            latency_ms=142,
        ),
    )

    write(
        "get_cases",
        CaseQueueResponse(
            metrics=QueueMetrics(
                awaiting_review=12,
                deterministic_conflicts=3,
                evidence_requested=2,
                median_time_in_queue_hours=6.5,
                versions=VERSIONS,
            ),
            items=(
                CaseSummary(
                    reason_sentence="Baris tindakan ini tidak punya catatan tindakan yang selesai.",
                    modes=(RiskMode.PHANTOM_OR_NO_PROCEDURE_EVIDENCE,),
                    case_id="CASE-0001",
                    participant_token="PSN-1002",
                    provider_token="PRV-01",
                    evidence_completeness=COMPLETENESS,
                    total_amount=Decimal("630000"),
                    currency="IDR",
                    created_at=T0,
                    band=PriorityBand.DETERMINISTIC_CONFLICT,
                    state=CaseState.SCREENED,
                    case_version=1,
                ),
                CaseSummary(
                    reason_sentence="Dokumentasi kunjungan ini sangat mirip dengan kunjungan lain.",
                    modes=(RiskMode.CLONED_DOCUMENTATION,),
                    case_id="CASE-0002",
                    participant_token="PSN-1005",
                    provider_token="PRV-02",
                    evidence_completeness=EvidenceCompleteness(
                        supported_lines=1,
                        total_lines=1,
                        missing_reference_count=0,
                        bundle_complete=True,
                    ),
                    total_amount=Decimal("150000"),
                    currency="IDR",
                    created_at=T0,
                    band=PriorityBand.NEEDS_CONTEXT,
                    state=CaseState.SCREENED,
                    case_version=1,
                ),
            ),
            page=PageInfo(page=1, page_size=25, total_items=2, total_pages=1),
        ),
    )

    write(
        "get_case_detail",
        CaseDetailResponse(
            case_id="CASE-0001",
            case_version=1,
            state=CaseState.SCREENED,
            participant_token="PSN-1002",
            provider_token="PRV-01",
            total_amount=Decimal("630000"),
            currency="IDR",
            encounter_start=datetime(2026, 7, 1, 8, 0, tzinfo=UTC),
            encounter_end=datetime(2026, 7, 1, 11, 0, tzinfo=UTC),
            primary_reason=PHANTOM_REASON,
            reasons=(PHANTOM_REASON,),
            band=BandExplanation(
                band=PriorityBand.DETERMINISTIC_CONFLICT,
                basis="Sebuah aturan integritas berversi dilanggar secara pasti.",
                caps_applied=(),
            ),
            lines=(
                ClaimLineView(
                    line_id="LN-P1",
                    code="89.7",
                    description="Layanan 89.7",
                    quantity=Decimal("1"),
                    line_amount=Decimal("150000"),
                    service_at=datetime(2026, 7, 1, 9, 0, tzinfo=UTC),
                    support_state="SUPPORTED",
                ),
                ClaimLineView(
                    line_id="LN-P2",
                    code="88.71",
                    description="Layanan 88.71",
                    quantity=Decimal("1"),
                    line_amount=Decimal("480000"),
                    service_at=datetime(2026, 7, 1, 10, 0, tzinfo=UTC),
                    support_state="UNSUPPORTED",
                ),
            ),
            timeline=(
                TimelineEvent(
                    occurred_at=datetime(2026, 7, 1, 8, 0, tzinfo=UTC),
                    kind="ENCOUNTER_START",
                    label="Kunjungan dimulai",
                    resource=EvidenceRefDto(
                        resource_type=ResourceType.ENCOUNTER,
                        resource_id="ENC-PH-1",
                        label="Kunjungan rawat jalan",
                    ),
                ),
                TimelineEvent(
                    occurred_at=datetime(2026, 7, 1, 9, 0, tzinfo=UTC),
                    kind="PROCEDURE",
                    label="Tindakan 89.7 selesai",
                    resource=EvidenceRefDto(
                        resource_type=ResourceType.PROCEDURE,
                        resource_id="PROC-P1",
                        label="Tindakan 89.7",
                    ),
                ),
                TimelineEvent(
                    occurred_at=datetime(2026, 7, 1, 10, 0, tzinfo=UTC),
                    kind="BILLED_WITHOUT_EVIDENCE",
                    label="Baris 88.71 ditagihkan tanpa catatan tindakan",
                    resource=EvidenceRefDto(
                        resource_type=ResourceType.CLAIM_LINE,
                        resource_id="LN-P2",
                        label="Baris tagihan 88.71",
                    ),
                ),
            ),
            comparisons=(),
            evidence_completeness=COMPLETENESS,
            suggested_action=None,
            versions=VERSIONS,
        ),
    )

    write(
        "get_case_detail_clone",
        CaseDetailResponse(
            case_id="CASE-0002",
            case_version=1,
            state=CaseState.SCREENED,
            participant_token="PSN-1005",
            provider_token="PRV-02",
            total_amount=Decimal("150000"),
            currency="IDR",
            encounter_start=datetime(2026, 7, 2, 14, 0, tzinfo=UTC),
            encounter_end=datetime(2026, 7, 2, 17, 0, tzinfo=UTC),
            primary_reason=(
                clone_reason := ReasonDto(
                    code=ReasonCode.NEAR_DUPLICATE_DOCUMENTATION,
                    mode=RiskMode.CLONED_DOCUMENTATION,
                    sentence="Dokumentasi kunjungan ini sangat mirip dengan kunjungan lain.",
                    deterministic=False,
                    evidence=(
                        EvidenceRefDto(
                            resource_type=ResourceType.DOCUMENT,
                            resource_id="DOC-CL-2",
                            label="Catatan klinis kunjungan ini",
                        ),
                    ),
                    counter_evidence=(
                        EvidenceRefDto(
                            resource_type=ResourceType.ENCOUNTER,
                            resource_id="ENC-CL-2",
                            label="Kunjungan pada peserta berbeda, 30 jam setelahnya",
                        ),
                    ),
                    component_scores={"char_ngram_similarity": 0.94},
                    ruleset_version=RULESET_VERSION,
                )
            ),
            reasons=(clone_reason,),
            band=BandExplanation(
                band=PriorityBand.NEEDS_CONTEXT,
                basis="Kemiripan dokumentasi tinggi, tanpa penguat dari keluarga bukti lain.",
                caps_applied=(
                    "Kemiripan teks saja tidak pernah cukup untuk mencapai pita tertinggi.",
                ),
            ),
            lines=(
                ClaimLineView(
                    line_id="LN-CL2",
                    code="89.7",
                    description="Layanan 89.7",
                    quantity=Decimal("1"),
                    line_amount=Decimal("150000"),
                    service_at=datetime(2026, 7, 2, 15, 0, tzinfo=UTC),
                    support_state="SUPPORTED",
                ),
            ),
            timeline=(),
            comparisons=(
                ComparisonCandidate(
                    candidate_case_id=None,
                    candidate_claim_id="CLM-CL-A",
                    fields=(
                        ComparisonField(
                            field_name="participant_token",
                            left_value="PSN-1005",
                            right_value="PSN-1004",
                            matches=False,
                        ),
                        ComparisonField(
                            field_name="provider_token",
                            left_value="PRV-02",
                            right_value="PRV-02",
                            matches=True,
                        ),
                        ComparisonField(
                            field_name="note_opening",
                            left_value="Pasien datang dengan keluhan nyeri tenggorokan sejak empat hari.",
                            right_value="Pasien datang dengan keluhan nyeri tenggorokan sejak tiga hari.",
                            matches=False,
                        ),
                    ),
                    similarity_components={"char_ngram": 0.94, "token_overlap": 0.91},
                    template_caveat=(
                        "Dokumentasi berbasis templat yang sah dapat menghasilkan kemiripan "
                        "setinggi ini. Periksa penguat dari bukti lain sebelum memutuskan."
                    ),
                ),
            ),
            evidence_completeness=EvidenceCompleteness(
                supported_lines=1, total_lines=1, missing_reference_count=0, bundle_complete=True
            ),
            suggested_action=None,
            versions=VERSIONS,
        ),
    )

    write(
        "post_disposition",
        DispositionResponse(
            event_id="EVT-0003",
            case_id="CASE-0001",
            new_state=CaseState.CONFIRMED_ANOMALY,
            new_case_version=2,
            recorded_at=datetime(2026, 7, 2, 10, 15, tzinfo=UTC),
        ),
    )

    write(
        "post_disposition_conflict",
        ErrorResponse(
            code=ErrorCode.CASE_VERSION_CONFLICT,
            detail=(
                "Kasus sudah berubah sejak layar dibuka (versi 1 → 2). "
                "Muat ulang lalu kirim ulang; isian Anda tidak hilang."
            ),
            issues=(),
        ),
    )

    write(
        "get_audit",
        AuditResponse(
            case_id="CASE-0001",
            events=(
                AuditEvent(
                    event_id="EVT-0001",
                    case_id="CASE-0001",
                    event_kind="CREATED",
                    actor_role="system",
                    state_before=None,
                    state_after=CaseState.NEW,
                    versions=VERSIONS,
                    occurred_at=datetime(2026, 7, 2, 9, 0, tzinfo=UTC),
                ),
                AuditEvent(
                    event_id="EVT-0002",
                    case_id="CASE-0001",
                    event_kind="SCREENED",
                    actor_role="system",
                    state_before=CaseState.NEW,
                    state_after=CaseState.SCREENED,
                    versions=VERSIONS,
                    occurred_at=datetime(2026, 7, 2, 9, 0, 1, tzinfo=UTC),
                ),
                AuditEvent(
                    event_id="EVT-0003",
                    case_id="CASE-0001",
                    event_kind="DISPOSITION",
                    actor_role="analyst",
                    action=DispositionAction.CONFIRM_ANOMALY,
                    structured_reason="Baris tagihan tidak didukung bukti, berkas lengkap.",
                    note="Sudah dicek ulang di rekam kunjungan, tidak ada catatan tindakan.",
                    evidence=(
                        EvidenceRefDto(
                            resource_type=ResourceType.CLAIM_LINE,
                            resource_id="LN-P2",
                            label="Baris tagihan 88.71",
                        ),
                    ),
                    state_before=CaseState.IN_REVIEW,
                    state_after=CaseState.CONFIRMED_ANOMALY,
                    versions=VERSIONS,
                    occurred_at=datetime(2026, 7, 2, 10, 15, tzinfo=UTC),
                ),
            ),
        ),
    )

    write(
        "get_evaluation",
        EvaluationResponse(
            run_id="RUN-0001",
            completed_at=datetime(2026, 9, 12, 8, 0, tzinfo=UTC),
            baselines=(
                BaselineMetrics(
                    baseline="B0_RANDOM",
                    macro_f1=0.11,
                    pr_auc=0.09,
                    precision_at_k=0.10,
                    recall_at_k=0.10,
                    false_positives_per_100_clean=48.0,
                ),
                BaselineMetrics(
                    baseline="B1_RULES_ONLY",
                    macro_f1=0.72,
                    pr_auc=0.68,
                    precision_at_k=0.81,
                    recall_at_k=0.55,
                    false_positives_per_100_clean=4.2,
                ),
                BaselineMetrics(
                    baseline="B2_STATISTICAL_ONLY",
                    macro_f1=0.44,
                    pr_auc=0.41,
                    precision_at_k=0.52,
                    recall_at_k=0.39,
                    false_positives_per_100_clean=11.7,
                ),
                BaselineMetrics(
                    baseline="HYBRID",
                    macro_f1=0.78,
                    pr_auc=0.75,
                    precision_at_k=0.88,
                    recall_at_k=0.63,
                    false_positives_per_100_clean=3.6,
                ),
            ),
            per_mode=(
                ModeMetrics(
                    mode=RiskMode.PHANTOM_OR_NO_PROCEDURE_EVIDENCE,
                    precision=0.91, recall=0.74, f1=0.82, support=300,
                ),
                ModeMetrics(
                    mode=RiskMode.REPEAT_BILLING,
                    precision=0.88, recall=0.71, f1=0.79, support=300,
                ),
                ModeMetrics(
                    mode=RiskMode.CLONED_DOCUMENTATION,
                    precision=0.66, recall=0.52, f1=0.58, support=300,
                ),
                ModeMetrics(
                    mode=RiskMode.UNBUNDLING_FRAGMENTATION,
                    precision=0.79, recall=0.61, f1=0.69, support=300,
                ),
            ),
            latency_p50_ms=118,
            latency_p95_ms=310,
            manifest=RunManifest(
                dataset_hash="d41f8c" + "0" * 58,
                generator_version="0.1.0",
                split_manifest_hash="7a2b9e" + "0" * 58,
                feature_version="0.1.0",
                ruleset_version=RULESET_VERSION,
                model_version="0.1.0",
                threshold_logic="calibrated on validation split, frozen before test evaluation",
                code_commit="0000000000000000000000000000000000000000",
                environment_hash="e5c3a1" + "0" * 58,
                artifact_hashes={
                    "metrics.json": "1a2b3c" + "0" * 58,
                    "per_mode.csv": "4d5e6f" + "0" * 58,
                },
            ),
            limitations=LimitationsCard(
                demonstrates=(
                    "Perangkat lunak membaca subset skema yang dipilih dengan benar.",
                    "Detektor menemukan kembali pola yang sengaja disuntikkan.",
                    "Rujukan bukti dan kejadian audit dapat dibangun ulang.",
                ),
                does_not_demonstrate=(
                    "Kesesuaian dengan sistem BPJS, E-Klaim, atau SATUSEHAT di lingkungan nyata.",
                    "Ketepatan atau prevalensi fraud JKN di dunia nyata.",
                    "Penghematan nasional atau dampak sebab-akibat.",
                    "Validitas klinis atau temuan hukum.",
                ),
            ),
            versions=VERSIONS,
        ),
    )

    print(f"Wrote {len(list(OUT.glob('*.json')))} API fixtures to {OUT}")


if __name__ == "__main__":
    main()

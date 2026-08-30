"""Build the five curated gold fixtures.

Run once; the JSON output is committed. Deterministic — no randomness, no clock reads — so
regenerating produces byte-identical files and a diff means something actually changed.

**These fixtures are excluded from every metric computation.** They exist to prove the engine
behaves correctly on known inputs, and a polished demo case must never influence a reported
number. `packages/data` enforces the exclusion; `test_gold_fixtures.py` asserts it here.

Each file wraps three things the engine must never see together:
  * `bundle`  — the canonical bundle under test (and `history`, prior claims in the store)
  * `demo`    — the presenter-facing scenario label, a sibling of the bundle, never a field
  * `expected_*` — the answer key, read only by tests
"""
from __future__ import annotations

import json
import pathlib
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from tilik_domain.canonical import (
    Account,
    CanonicalBundle,
    CareType,
    ChargeItem,
    ClaimHeader,
    ClaimLine,
    ClaimStatus,
    Condition,
    DemoMetadata,
    DiagnosticEvent,
    DocumentRef,
    Encounter,
    EncounterStatus,
    EventStatus,
    Invoice,
    Procedure,
    Provenance,
    ResourceRef,
    ResourceType,
    SourceType,
    VerificationStatus,
)
from tilik_domain.reasons import ReasonCode

OUT_DIR = pathlib.Path(__file__).parent / "gold"
BASE = datetime(2026, 7, 1, 8, 0, tzinfo=UTC)
SYS_ICD = "http://hl7.org/fhir/sid/icd-10"
SYS_PROC = "http://terminology.kemkes.go.id/CodeSystem/icd9cm"


def _hash(text: str) -> str:
    """Stable content hash. Deliberately not a crypto hash — it identifies text, not secrets."""
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:32]


def _provenance(resource_id: str, resource_type: ResourceType) -> Provenance:
    return Provenance(
        resource_id=resource_id,
        resource_type=resource_type,
        source_type=SourceType.GOLD_FIXTURE,
        last_updated_at=BASE,
    )


def _encounter(enc_id: str, participant: str, provider: str, offset_h: int) -> Encounter:
    return Encounter(
        encounter_id=enc_id,
        class_code="AMB",
        status=EncounterStatus.FINISHED,
        start_at=BASE + timedelta(hours=offset_h),
        end_at=BASE + timedelta(hours=offset_h + 3),
        provider_id=provider,
        location_id="LOC-01",
        participant_id=participant,
    )


def _procedure(proc_id: str, code: str, enc_id: str, offset_h: int, status: EventStatus) -> Procedure:
    return Procedure(
        procedure_id=proc_id,
        code_system=SYS_PROC,
        code=code,
        status=status,
        performed_at=BASE + timedelta(hours=offset_h),
        performer_id="PRACT-01",
        location_id="LOC-01",
        encounter_id=enc_id,
    )


def _charge(ci_id: str, code: str, enc_id: str, amount: str, offset_h: int) -> ChargeItem:
    return ChargeItem(
        charge_item_id=ci_id,
        account_id="ACC-01",
        code_system=SYS_PROC,
        code=code,
        quantity=Decimal(1),
        unit_price=Decimal(amount),
        total_amount=Decimal(amount),
        occurred_at=BASE + timedelta(hours=offset_h),
        encounter_id=enc_id,
    )


def _line(
    line_id: str,
    claim_id: str,
    code: str,
    amount: str,
    enc_offset_h: int,
    supporting: tuple[ResourceRef, ...],
    charge_ref: str | None = None,
) -> ClaimLine:
    return ClaimLine(
        line_id=line_id,
        claim_id=claim_id,
        code_system=SYS_PROC,
        code=code,
        description=f"Layanan {code}",
        quantity=Decimal(1),
        unit_price=Decimal(amount),
        line_amount=Decimal(amount),
        service_at=BASE + timedelta(hours=enc_offset_h),
        charge_item_ref=(
            ResourceRef(resource_type=ResourceType.CHARGE_ITEM, resource_id=charge_ref)
            if charge_ref
            else None
        ),
        supporting_refs=supporting,
    )


def _proc_ref(proc_id: str) -> ResourceRef:
    return ResourceRef(resource_type=ResourceType.PROCEDURE, resource_id=proc_id)


def _assemble(
    bundle_id: str,
    claim_id: str,
    participant: str,
    provider: str,
    episode: str | None,
    lines: tuple[ClaimLine, ...],
    encounters: tuple[Encounter, ...],
    procedures: tuple[Procedure, ...],
    charge_items: tuple[ChargeItem, ...],
    documents: tuple[DocumentRef, ...] = (),
    diagnostics: tuple[DiagnosticEvent, ...] = (),
    submitted_offset_h: int = 24,
) -> CanonicalBundle:
    total = sum((line.line_amount for line in lines), Decimal(0))
    claim = ClaimHeader(
        claim_id=claim_id,
        participant_id=participant,
        provider_id=provider,
        encounter_id=encounters[0].encounter_id,
        episode_id=episode,
        care_type=CareType.OUTPATIENT,
        submitted_at=BASE + timedelta(hours=submitted_offset_h),
        status=ClaimStatus.ACTIVE,
        total_amount=total,
    )
    provenance = tuple(
        [_provenance(claim_id, ResourceType.CLAIM)]
        + [_provenance(line.line_id, ResourceType.CLAIM_LINE) for line in lines]
        + [_provenance(enc.encounter_id, ResourceType.ENCOUNTER) for enc in encounters]
        + [_provenance(p.procedure_id, ResourceType.PROCEDURE) for p in procedures]
        + [_provenance(d.document_id, ResourceType.DOCUMENT) for d in documents]
    )
    return CanonicalBundle(
        bundle_id=bundle_id,
        claim=claim,
        lines=lines,
        encounters=encounters,
        conditions=(
            Condition(
                condition_id=f"COND-{claim_id}",
                code_system=SYS_ICD,
                code="J06.9",
                recorded_at=encounters[0].start_at,
                verification_status=VerificationStatus.CONFIRMED,
                encounter_id=encounters[0].encounter_id,
            ),
        ),
        procedures=procedures,
        diagnostics=diagnostics,
        documents=documents,
        accounts=(
            Account(
                account_id="ACC-01", participant_id=participant, provider_id=provider, status="active"
            ),
        ),
        charge_items=charge_items,
        invoices=(
            Invoice(
                invoice_id=f"INV-{claim_id}",
                account_id="ACC-01",
                total_amount=total,
                issued_at=claim.submitted_at,
                charge_item_refs=tuple(
                    ResourceRef(
                        resource_type=ResourceType.CHARGE_ITEM, resource_id=ci.charge_item_id
                    )
                    for ci in charge_items
                ),
            ),
        ),
        provenance=provenance,
    )


def _write(
    name: str,
    demo: DemoMetadata,
    bundle: CanonicalBundle,
    expected_codes: tuple[ReasonCode, ...],
    evidence_complete: bool,
    history: tuple[CanonicalBundle, ...] = (),
) -> None:
    payload = {
        "scenario": name,
        "demo": json.loads(demo.model_dump_json()),
        "history": [json.loads(b.model_dump_json()) for b in history],
        "bundle": json.loads(bundle.model_dump_json()),
        "expected_reason_codes": [str(c) for c in expected_codes],
        "expected_evidence_complete": evidence_complete,
    }
    path = OUT_DIR / f"{name}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"  {name:12s} lines={len(bundle.lines)} history={len(history)} expected={len(expected_codes)}")


NOTE_A = (
    "Pasien datang dengan keluhan nyeri tenggorokan sejak tiga hari. "
    "Pemeriksaan fisik menunjukkan faring hiperemis tanpa eksudat. "
    "Diberikan terapi simtomatik dan edukasi kebersihan tangan."
)
NOTE_B = (
    "Pasien datang dengan keluhan batuk sejak dua minggu disertai demam ringan. "
    "Auskultasi paru terdengar ronki basah di basal kanan. "
    "Direncanakan pemeriksaan penunjang lanjutan."
)


def build_clean() -> None:
    """Every billed line has a completed supporting procedure. No detector should fire."""
    enc = _encounter("ENC-CLEAN-1", "PSN-1001", "PRV-01", 0)
    procs = (
        _procedure("PROC-C1", "89.7", enc.encounter_id, 1, EventStatus.COMPLETED),
        _procedure("PROC-C2", "93.94", enc.encounter_id, 2, EventStatus.COMPLETED),
    )
    charges = (_charge("CI-C1", "89.7", enc.encounter_id, "150000", 1),
               _charge("CI-C2", "93.94", enc.encounter_id, "225000", 2))
    lines = (
        _line("LN-C1", "CLM-CLEAN", "89.7", "150000", 1, (_proc_ref("PROC-C1"),), "CI-C1"),
        _line("LN-C2", "CLM-CLEAN", "93.94", "225000", 2, (_proc_ref("PROC-C2"),), "CI-C2"),
    )
    bundle = _assemble("BND-CLEAN", "CLM-CLEAN", "PSN-1001", "PRV-01", "EPS-C1",
                       lines, (enc,), procs, charges)
    _write("clean",
           DemoMetadata(bundle_id="BND-CLEAN", scenario_label="Bersih",
                        description="Seluruh baris tagihan punya bukti pendukung yang konsisten."),
           bundle, (), evidence_complete=True)


def build_phantom() -> None:
    """One billed procedure line has no completed Procedure, and the bundle is complete.

    Completeness is what makes this actionable: the evidence is absent, not merely unsent.
    The incomplete-bundle counterpart is a different case entirely and must route to
    'request evidence' instead — see brief/02 § 4.3.
    """
    enc = _encounter("ENC-PH-1", "PSN-1002", "PRV-01", 0)
    procs = (_procedure("PROC-P1", "89.7", enc.encounter_id, 1, EventStatus.COMPLETED),)
    charges = (_charge("CI-P1", "89.7", enc.encounter_id, "150000", 1),
               _charge("CI-P2", "88.71", enc.encounter_id, "480000", 2))
    lines = (
        _line("LN-P1", "CLM-PH", "89.7", "150000", 1, (_proc_ref("PROC-P1"),), "CI-P1"),
        # No supporting_refs and no matching Procedure resource anywhere in the bundle.
        _line("LN-P2", "CLM-PH", "88.71", "480000", 2, (), "CI-P2"),
    )
    bundle = _assemble("BND-PHANTOM", "CLM-PH", "PSN-1002", "PRV-01", "EPS-P1",
                       lines, (enc,), procs, charges)
    _write("phantom",
           DemoMetadata(bundle_id="BND-PHANTOM", scenario_label="Tagihan tanpa bukti tindakan",
                        description="Satu baris tindakan tidak punya catatan tindakan yang selesai."),
           bundle, (ReasonCode.LINE_WITHOUT_COMPLETED_PROCEDURE,), evidence_complete=True)


def build_repeat() -> None:
    """A second claim for the same participant, provider, and episode with overlapping lines.

    Detection needs the prior claim, which lives in the store — so it ships as `history`.
    """
    enc_prior = _encounter("ENC-RP-1", "PSN-1003", "PRV-01", 0)
    procs_prior = (_procedure("PROC-R1", "89.7", enc_prior.encounter_id, 1, EventStatus.COMPLETED),)
    charges_prior = (_charge("CI-R1", "89.7", enc_prior.encounter_id, "150000", 1),)
    lines_prior = (_line("LN-R1", "CLM-RP-A", "89.7", "150000", 1, (_proc_ref("PROC-R1"),), "CI-R1"),)
    prior = _assemble("BND-REPEAT-PRIOR", "CLM-RP-A", "PSN-1003", "PRV-01", "EPS-R1",
                      lines_prior, (enc_prior,), procs_prior, charges_prior)

    # Same episode, same line code and amount, different IDs and a slightly shifted timestamp.
    enc_dup = _encounter("ENC-RP-2", "PSN-1003", "PRV-01", 2)
    procs_dup = (_procedure("PROC-R2", "89.7", enc_dup.encounter_id, 3, EventStatus.COMPLETED),)
    charges_dup = (_charge("CI-R2", "89.7", enc_dup.encounter_id, "150000", 3),)
    lines_dup = (_line("LN-R2", "CLM-RP-B", "89.7", "150000", 3, (_proc_ref("PROC-R2"),), "CI-R2"),)
    dup = _assemble("BND-REPEAT", "CLM-RP-B", "PSN-1003", "PRV-01", "EPS-R1",
                    lines_dup, (enc_dup,), procs_dup, charges_dup, submitted_offset_h=26)
    _write("repeat",
           DemoMetadata(bundle_id="BND-REPEAT", scenario_label="Tagihan berulang",
                        description="Klaim kedua pada episode yang sama dengan baris bertumpang tindih."),
           dup, (ReasonCode.OVERLAPPING_CLAIM_SAME_EPISODE,), evidence_complete=True,
           history=(prior,))


def build_clone() -> None:
    """Near-identical narrative across two different participants and encounters.

    `expected_evidence_complete` stays True, but this reason is non-deterministic: legitimate
    template use produces high similarity too, so it can never alone reach the top band.
    """
    enc_prior = _encounter("ENC-CL-1", "PSN-1004", "PRV-02", 0)
    doc_prior = DocumentRef(document_id="DOC-CL-1", kind="clinical-note", text=NOTE_A,
                            text_hash=_hash(NOTE_A), author_id="PRACT-02",
                            authored_at=BASE + timedelta(hours=1), encounter_id=enc_prior.encounter_id)
    procs_prior = (_procedure("PROC-CL1", "89.7", enc_prior.encounter_id, 1, EventStatus.COMPLETED),)
    charges_prior = (_charge("CI-CL1", "89.7", enc_prior.encounter_id, "150000", 1),)
    lines_prior = (_line("LN-CL1", "CLM-CL-A", "89.7", "150000", 1, (_proc_ref("PROC-CL1"),), "CI-CL1"),)
    prior = _assemble("BND-CLONE-PRIOR", "CLM-CL-A", "PSN-1004", "PRV-02", "EPS-CL1",
                      lines_prior, (enc_prior,), procs_prior, charges_prior, documents=(doc_prior,))

    # Different participant; note copied with one word changed.
    cloned_text = NOTE_A.replace("tiga hari", "empat hari")
    enc_dup = _encounter("ENC-CL-2", "PSN-1005", "PRV-02", 30)
    doc_dup = DocumentRef(document_id="DOC-CL-2", kind="clinical-note", text=cloned_text,
                          text_hash=_hash(cloned_text), author_id="PRACT-02",
                          authored_at=BASE + timedelta(hours=31), encounter_id=enc_dup.encounter_id)
    procs_dup = (_procedure("PROC-CL2", "89.7", enc_dup.encounter_id, 31, EventStatus.COMPLETED),)
    charges_dup = (_charge("CI-CL2", "89.7", enc_dup.encounter_id, "150000", 31),)
    lines_dup = (_line("LN-CL2", "CLM-CL-B", "89.7", "150000", 31, (_proc_ref("PROC-CL2"),), "CI-CL2"),)
    dup = _assemble("BND-CLONE", "CLM-CL-B", "PSN-1005", "PRV-02", "EPS-CL2",
                    lines_dup, (enc_dup,), procs_dup, charges_dup, documents=(doc_dup,),
                    submitted_offset_h=54)
    _write("clone",
           DemoMetadata(bundle_id="BND-CLONE", scenario_label="Dokumentasi salinan",
                        description="Catatan klinis nyaris identik dengan kunjungan peserta lain."),
           dup, (ReasonCode.NEAR_DUPLICATE_DOCUMENTATION,), evidence_complete=True,
           history=(prior,))


def build_unbundled() -> None:
    """One coherent episode split across two temporally adjacent claims."""
    enc_a = _encounter("ENC-UB-1", "PSN-1006", "PRV-03", 0)
    procs_a = (_procedure("PROC-U1", "89.7", enc_a.encounter_id, 1, EventStatus.COMPLETED),)
    charges_a = (_charge("CI-U1", "89.7", enc_a.encounter_id, "150000", 1),)
    lines_a = (_line("LN-U1", "CLM-UB-A", "89.7", "150000", 1, (_proc_ref("PROC-U1"),), "CI-U1"),)
    first = _assemble("BND-UNBUNDLED-PRIOR", "CLM-UB-A", "PSN-1006", "PRV-03", "EPS-U1",
                      lines_a, (enc_a,), procs_a, charges_a)

    # Same episode, one hour later, carrying the rest of what belonged in one claim.
    enc_b = _encounter("ENC-UB-2", "PSN-1006", "PRV-03", 1)
    procs_b = (
        _procedure("PROC-U2", "93.94", enc_b.encounter_id, 2, EventStatus.COMPLETED),
        _procedure("PROC-U3", "88.71", enc_b.encounter_id, 2, EventStatus.COMPLETED),
    )
    charges_b = (_charge("CI-U2", "93.94", enc_b.encounter_id, "225000", 2),
                 _charge("CI-U3", "88.71", enc_b.encounter_id, "480000", 2))
    lines_b = (
        _line("LN-U2", "CLM-UB-B", "93.94", "225000", 2, (_proc_ref("PROC-U2"),), "CI-U2"),
        _line("LN-U3", "CLM-UB-B", "88.71", "480000", 2, (_proc_ref("PROC-U3"),), "CI-U3"),
    )
    second = _assemble("BND-UNBUNDLED", "CLM-UB-B", "PSN-1006", "PRV-03", "EPS-U1",
                       lines_b, (enc_b,), procs_b, charges_b, submitted_offset_h=25)
    _write("unbundled",
           DemoMetadata(bundle_id="BND-UNBUNDLED", scenario_label="Episode terpecah",
                        description="Layanan satu episode dipecah ke dua klaim berdekatan waktu."),
           second, (ReasonCode.EPISODE_SPLIT_ACROSS_CLAIMS,), evidence_complete=True,
           history=(first,))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("Building gold fixtures:")
    build_clean()
    build_phantom()
    build_repeat()
    build_clone()
    build_unbundled()
    print(f"Wrote {len(list(OUT_DIR.glob('*.json')))} fixtures to {OUT_DIR}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Generate hundreds of dummy ingest bundles for load/demo testing.

    cd apps/backend && uv run python scripts/generate_bulk_fixtures.py
    cd apps/backend && uv run python scripts/generate_bulk_fixtures.py 500

Output:
  tests/fixtures/bulk_demo.json        — array of GoldFixture-shaped objects (untuk seed script)
  tests/fixtures/bulk_bundles/         — satu file per bundle, berisi CanonicalBundle saja (untuk UI upload)
"""
from __future__ import annotations

import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

ICD9_PROCEDURES = [
    ("89.7",  "Pemeriksaan Kardiovaskular",   150_000),
    ("93.94", "Terapi Pernapasan",             225_000),
    ("88.71", "USG Kepala dan Leher",          480_000),
    ("99.04", "Transfusi Packed Red Cells",    750_000),
    ("93.11", "Latihan Fisioterapi",           175_000),
    ("87.41", "Foto Rontgen Toraks",           200_000),
    ("89.52", "Elektrokardiogram",             120_000),
    ("96.04", "Pemasangan Selang Nasogastrik", 100_000),
    ("99.18", "Injeksi Vaksin",                 85_000),
    ("93.59", "Terapi Fisik Lainnya",          160_000),
    ("88.76", "USG Abdomen",                   350_000),
    ("89.39", "Pemeriksaan Fungsi Jantung",    280_000),
    ("99.23", "Injeksi Steroid",               130_000),
    ("93.22", "Latihan Penguatan Otot",        145_000),
    ("88.01", "Tomografi Kepala",              900_000),
    ("87.03", "CT Scan Toraks",                850_000),
    ("99.10", "Transfusi Darah Segar",         680_000),
    ("89.61", "Pemantauan EEG",                320_000),
    ("93.97", "Inhalasi Obat",                 115_000),
    ("96.59", "Irigasi Saluran Lain",           90_000),
]

ICD10_DIAGNOSES = [
    ("J06.9", "Infeksi Saluran Pernapasan Atas Akut"),
    ("I10",   "Hipertensi Esensial"),
    ("K29.7", "Gastritis, tidak spesifik"),
    ("M54.5", "Nyeri Punggung Bawah"),
    ("E11.9", "Diabetes Melitus Tipe 2"),
    ("J18.9", "Pneumonia, tidak spesifik"),
    ("N39.0", "Infeksi Saluran Kemih"),
    ("A09",   "Diare Akut"),
    ("J45.9", "Asma, tidak spesifik"),
    ("K35.9", "Apendisitis Akut"),
    ("I50.9", "Gagal Jantung, tidak spesifik"),
    ("G43.9", "Migrain, tidak spesifik"),
    ("L23.9", "Dermatitis Kontak Alergik"),
    ("B34.9", "Infeksi Virus, tidak spesifik"),
    ("R51",   "Sakit Kepala"),
    ("R05",   "Batuk"),
    ("R50.9", "Demam, tidak spesifik"),
    ("Z00.0", "Pemeriksaan Medis Umum"),
]

PROVIDERS = ["PRV-01", "PRV-02", "PRV-03", "PRV-04", "PRV-05"]
LOCATIONS = ["LOC-01", "LOC-02", "LOC-03", "LOC-04"]
PRACTITIONERS = ["PRACT-01", "PRACT-02", "PRACT-03"]

SCENARIO_LABELS = {
    "clean":      "Bersih",
    "phantom":    "Tagihan tanpa bukti tindakan",
    "repeat":     "Tagihan berulang",
    "clone":      "Kloning tagihan pasien lain",
    "unbundled":  "Unbundling komponen",
}

SCENARIO_DESCRIPTIONS = {
    "clean":     "Seluruh baris tagihan punya bukti pendukung yang konsisten.",
    "phantom":   "Satu atau lebih baris tindakan tidak punya catatan tindakan yang selesai.",
    "repeat":    "Klaim ini menagihkan prosedur yang sudah pernah ditagih sebelumnya.",
    "clone":     "Pola tagihan identik dengan klaim pasien lain pada tanggal yang sama.",
    "unbundled": "Komponen prosedur ditagih terpisah padahal seharusnya satu paket.",
}

EXPECTED_CODES = {
    "clean":     [],
    "phantom":   ["LINE_WITHOUT_COMPLETED_PROCEDURE"],
    "repeat":    ["REPEAT_BILLED_LINE"],
    "clone":     ["CLONE_OF_BASELINE"],
    "unbundled": ["UNBUNDLED_COMPONENTS"],
}

CODE_SYS_ICD9 = "http://terminology.kemkes.go.id/CodeSystem/icd9cm"
CODE_SYS_ICD10 = "http://hl7.org/fhir/sid/icd-10"
SCHEMA_VERSION = "0.1.0"
CURRENCY = "IDR"

BASE_DATE = datetime(2026, 1, 1, tzinfo=timezone.utc)


def fmt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def make_provenance(resource_id: str, resource_type: str, at: datetime) -> dict:
    return {
        "bundle_hash": None,
        "last_updated_at": fmt(at),
        "resource_id": resource_id,
        "resource_type": resource_type,
        "schema_version": SCHEMA_VERSION,
        "source_type": "synthetic_generator",
    }


# ---------------------------------------------------------------------------
# Bundle builders per scenario
# ---------------------------------------------------------------------------

def _day(seed: int) -> datetime:
    """One visit day per bundle, spread across 8 months."""
    return BASE_DATE + timedelta(days=seed % 240)


def build_clean(idx: int, rng: random.Random) -> dict:
    day = _day(idx)
    psn = f"PSN-{2000 + idx}"
    prv = rng.choice(PROVIDERS)
    loc = rng.choice(LOCATIONS)
    pract = rng.choice(PRACTITIONERS)
    acc = f"ACC-{idx:04d}"
    enc = f"ENC-CL-{idx}"
    eps = f"EPS-CL-{idx}"
    clm = f"CLM-CL-{idx}"
    bnd = f"BND-CL-{idx}"
    diag_code, _ = rng.choice(ICD10_DIAGNOSES)

    num_lines = rng.randint(1, 3)
    chosen = rng.sample(ICD9_PROCEDURES, num_lines)

    charge_items, lines, procedures, prov = [], [], [], []
    total = 0

    visit_start = day.replace(hour=8)
    for li, (code, desc, price) in enumerate(chosen, 1):
        ci_id   = f"CI-CL-{idx}-{li}"
        ln_id   = f"LN-CL-{idx}-{li}"
        proc_id = f"PROC-CL-{idx}-{li}"
        svc_at  = visit_start + timedelta(hours=li)
        total  += price

        charge_items.append({
            "account_id":     acc,
            "charge_item_id": ci_id,
            "code":           code,
            "code_system":    CODE_SYS_ICD9,
            "encounter_id":   enc,
            "occurred_at":    fmt(svc_at),
            "quantity":       "1",
            "total_amount":   str(price),
            "unit_price":     str(price),
        })
        lines.append({
            "charge_item_ref": {"resource_id": ci_id, "resource_type": "ChargeItem"},
            "claim_id":        clm,
            "code":            code,
            "code_system":     CODE_SYS_ICD9,
            "description":     f"Layanan {code}",
            "line_amount":     str(price),
            "line_id":         ln_id,
            "quantity":        "1",
            "service_at":      fmt(svc_at),
            "supporting_refs": [{"resource_id": proc_id, "resource_type": "Procedure"}],
            "unit_price":      str(price),
        })
        procedures.append({
            "code":         code,
            "code_system":  CODE_SYS_ICD9,
            "encounter_id": enc,
            "location_id":  loc,
            "performed_at": fmt(svc_at),
            "performer_id": pract,
            "procedure_id": proc_id,
            "status":       "completed",
        })
        prov.append(make_provenance(ln_id, "ClaimLine", day))
        prov.append(make_provenance(proc_id, "Procedure", day))

    submitted_at = day + timedelta(days=1, hours=8)
    prov.insert(0, make_provenance(clm, "Claim", day))
    prov.insert(1, make_provenance(enc, "Encounter", day))

    bundle = {
        "accounts": [{"account_id": acc, "participant_id": psn, "provider_id": prv, "status": "active"}],
        "bundle_id": bnd,
        "charge_items": charge_items,
        "claim": {
            "care_type":     rng.choice(["outpatient", "inpatient"]),
            "claim_id":      clm,
            "currency":      CURRENCY,
            "encounter_id":  enc,
            "episode_id":    eps,
            "participant_id": psn,
            "provider_id":   prv,
            "status":        "active",
            "submitted_at":  fmt(submitted_at),
            "total_amount":  str(total),
        },
        "conditions": [{
            "code":                diag_code,
            "code_system":         CODE_SYS_ICD10,
            "condition_id":        f"COND-CL-{idx}",
            "encounter_id":        enc,
            "onset_at":            None,
            "recorded_at":         fmt(visit_start),
            "verification_status": "confirmed",
        }],
        "diagnostics": [],
        "documents":   [],
        "encounters": [{
            "class_code":    "AMB",
            "encounter_id":  enc,
            "end_at":        fmt(visit_start + timedelta(hours=num_lines + 1)),
            "location_id":   loc,
            "participant_id": psn,
            "provider_id":   prv,
            "start_at":      fmt(visit_start),
            "status":        "finished",
        }],
        "invoices": [{
            "account_id": acc,
            "charge_item_refs": [{"resource_id": ci["charge_item_id"], "resource_type": "ChargeItem"} for ci in charge_items],
            "invoice_id":  f"INV-CL-{idx}",
            "issued_at":   fmt(submitted_at),
            "total_amount": str(total),
        }],
        "lines":       lines,
        "medications": [],
        "procedures":  procedures,
        "provenance":  prov,
    }
    return {
        "scenario": "clean",
        "demo": {"bundle_id": bnd, "description": SCENARIO_DESCRIPTIONS["clean"], "scenario_label": SCENARIO_LABELS["clean"]},
        "history": [],
        "bundle": bundle,
        "expected_reason_codes": EXPECTED_CODES["clean"],
        "expected_evidence_complete": True,
    }


def build_phantom(idx: int, rng: random.Random) -> dict:
    """One line has no matching completed procedure."""
    day = _day(idx)
    psn = f"PSN-{3000 + idx}"
    prv = rng.choice(PROVIDERS)
    loc = rng.choice(LOCATIONS)
    pract = rng.choice(PRACTITIONERS)
    acc = f"ACC-PH-{idx:04d}"
    enc = f"ENC-PH-{idx}"
    eps = f"EPS-PH-{idx}"
    clm = f"CLM-PH-{idx}"
    bnd = f"BND-PH-{idx}"
    diag_code, _ = rng.choice(ICD10_DIAGNOSES)

    num_lines = rng.randint(2, 3)
    chosen = rng.sample(ICD9_PROCEDURES, num_lines)
    ghost_idx = rng.randint(0, num_lines - 1)  # this line has no procedure

    charge_items, lines, procedures, prov = [], [], [], []
    total = 0
    visit_start = day.replace(hour=8)

    for li, (code, desc, price) in enumerate(chosen, 1):
        ci_id   = f"CI-PH-{idx}-{li}"
        ln_id   = f"LN-PH-{idx}-{li}"
        proc_id = f"PROC-PH-{idx}-{li}"
        svc_at  = visit_start + timedelta(hours=li)
        total  += price
        is_ghost = (li - 1 == ghost_idx)

        charge_items.append({
            "account_id":     acc,
            "charge_item_id": ci_id,
            "code":           code,
            "code_system":    CODE_SYS_ICD9,
            "encounter_id":   enc,
            "occurred_at":    fmt(svc_at),
            "quantity":       "1",
            "total_amount":   str(price),
            "unit_price":     str(price),
        })
        lines.append({
            "charge_item_ref": {"resource_id": ci_id, "resource_type": "ChargeItem"},
            "claim_id":        clm,
            "code":            code,
            "code_system":     CODE_SYS_ICD9,
            "description":     f"Layanan {code}",
            "line_amount":     str(price),
            "line_id":         ln_id,
            "quantity":        "1",
            "service_at":      fmt(svc_at),
            "supporting_refs": [] if is_ghost else [{"resource_id": proc_id, "resource_type": "Procedure"}],
            "unit_price":      str(price),
        })
        if not is_ghost:
            procedures.append({
                "code":         code,
                "code_system":  CODE_SYS_ICD9,
                "encounter_id": enc,
                "location_id":  loc,
                "performed_at": fmt(svc_at),
                "performer_id": pract,
                "procedure_id": proc_id,
                "status":       "completed",
            })
            prov.append(make_provenance(proc_id, "Procedure", day))
        prov.append(make_provenance(ln_id, "ClaimLine", day))

    submitted_at = day + timedelta(days=1, hours=8)
    prov.insert(0, make_provenance(clm, "Claim", day))
    prov.insert(1, make_provenance(enc, "Encounter", day))

    bundle = {
        "accounts": [{"account_id": acc, "participant_id": psn, "provider_id": prv, "status": "active"}],
        "bundle_id": bnd,
        "charge_items": charge_items,
        "claim": {
            "care_type":     "outpatient",
            "claim_id":      clm,
            "currency":      CURRENCY,
            "encounter_id":  enc,
            "episode_id":    eps,
            "participant_id": psn,
            "provider_id":   prv,
            "status":        "active",
            "submitted_at":  fmt(submitted_at),
            "total_amount":  str(total),
        },
        "conditions": [{
            "code":                diag_code,
            "code_system":         CODE_SYS_ICD10,
            "condition_id":        f"COND-PH-{idx}",
            "encounter_id":        enc,
            "onset_at":            None,
            "recorded_at":         fmt(visit_start),
            "verification_status": "confirmed",
        }],
        "diagnostics": [],
        "documents":   [],
        "encounters": [{
            "class_code":    "AMB",
            "encounter_id":  enc,
            "end_at":        fmt(visit_start + timedelta(hours=num_lines + 1)),
            "location_id":   loc,
            "participant_id": psn,
            "provider_id":   prv,
            "start_at":      fmt(visit_start),
            "status":        "finished",
        }],
        "invoices": [{
            "account_id": acc,
            "charge_item_refs": [{"resource_id": ci["charge_item_id"], "resource_type": "ChargeItem"} for ci in charge_items],
            "invoice_id":  f"INV-PH-{idx}",
            "issued_at":   fmt(submitted_at),
            "total_amount": str(total),
        }],
        "lines":       lines,
        "medications": [],
        "procedures":  procedures,
        "provenance":  prov,
    }
    return {
        "scenario": "phantom",
        "demo": {"bundle_id": bnd, "description": SCENARIO_DESCRIPTIONS["phantom"], "scenario_label": SCENARIO_LABELS["phantom"]},
        "history": [],
        "bundle": bundle,
        "expected_reason_codes": EXPECTED_CODES["phantom"],
        "expected_evidence_complete": True,
    }


def build_repeat(idx: int, rng: random.Random) -> dict:
    """Current bundle re-bills a procedure already submitted in history."""
    day = _day(idx)
    prior_day = day - timedelta(days=rng.randint(1, 14))
    psn = f"PSN-{4000 + idx}"
    prv = rng.choice(PROVIDERS)
    loc = rng.choice(LOCATIONS)
    pract = rng.choice(PRACTITIONERS)
    acc = f"ACC-RP-{idx:04d}"
    eps = f"EPS-RP-{idx}"
    diag_code, _ = rng.choice(ICD10_DIAGNOSES)
    shared_proc = rng.choice(ICD9_PROCEDURES)
    code, desc, price = shared_proc

    def _make_enc_bundle(suffix: str, day_dt: datetime, enc_sfx: str) -> dict:
        enc  = f"ENC-RP-{idx}-{enc_sfx}"
        clm  = f"CLM-RP-{idx}-{suffix}"
        ci   = f"CI-RP-{idx}-{suffix}"
        ln   = f"LN-RP-{idx}-{suffix}"
        proc = f"PROC-RP-{idx}-{suffix}"
        acc_ = f"ACC-RP-{idx:04d}"
        visit_start = day_dt.replace(hour=9)
        submitted = day_dt + timedelta(days=1, hours=8)
        return {
            "accounts": [{"account_id": acc_, "participant_id": psn, "provider_id": prv, "status": "active"}],
            "bundle_id": f"BND-RP-{idx}-{suffix}",
            "charge_items": [{
                "account_id": acc_, "charge_item_id": ci, "code": code,
                "code_system": CODE_SYS_ICD9, "encounter_id": enc,
                "occurred_at": fmt(visit_start), "quantity": "1",
                "total_amount": str(price), "unit_price": str(price),
            }],
            "claim": {
                "care_type": "outpatient", "claim_id": clm, "currency": CURRENCY,
                "encounter_id": enc, "episode_id": eps, "participant_id": psn,
                "provider_id": prv, "status": "active",
                "submitted_at": fmt(submitted), "total_amount": str(price),
            },
            "conditions": [{
                "code": diag_code, "code_system": CODE_SYS_ICD10,
                "condition_id": f"COND-RP-{idx}-{suffix}", "encounter_id": enc,
                "onset_at": None, "recorded_at": fmt(visit_start),
                "verification_status": "confirmed",
            }],
            "diagnostics": [], "documents": [],
            "encounters": [{
                "class_code": "AMB", "encounter_id": enc,
                "end_at": fmt(visit_start + timedelta(hours=2)),
                "location_id": loc, "participant_id": psn, "provider_id": prv,
                "start_at": fmt(visit_start), "status": "finished",
            }],
            "invoices": [{
                "account_id": acc_,
                "charge_item_refs": [{"resource_id": ci, "resource_type": "ChargeItem"}],
                "invoice_id": f"INV-RP-{idx}-{suffix}",
                "issued_at": fmt(submitted), "total_amount": str(price),
            }],
            "lines": [{
                "charge_item_ref": {"resource_id": ci, "resource_type": "ChargeItem"},
                "claim_id": clm, "code": code, "code_system": CODE_SYS_ICD9,
                "description": f"Layanan {code}", "line_amount": str(price),
                "line_id": ln, "quantity": "1", "service_at": fmt(visit_start),
                "supporting_refs": [{"resource_id": proc, "resource_type": "Procedure"}],
                "unit_price": str(price),
            }],
            "medications": [],
            "procedures": [{
                "code": code, "code_system": CODE_SYS_ICD9,
                "encounter_id": enc, "location_id": loc,
                "performed_at": fmt(visit_start), "performer_id": pract,
                "procedure_id": proc, "status": "completed",
            }],
            "provenance": [
                make_provenance(clm, "Claim", day_dt),
                make_provenance(enc, "Encounter", day_dt),
                make_provenance(ln, "ClaimLine", day_dt),
                make_provenance(proc, "Procedure", day_dt),
            ],
        }

    history_bundle = _make_enc_bundle("A", prior_day, "A")
    current_bundle = _make_enc_bundle("B", day, "B")
    bnd = current_bundle["bundle_id"]

    return {
        "scenario": "repeat",
        "demo": {"bundle_id": bnd, "description": SCENARIO_DESCRIPTIONS["repeat"], "scenario_label": SCENARIO_LABELS["repeat"]},
        "history": [history_bundle],
        "bundle": current_bundle,
        "expected_reason_codes": EXPECTED_CODES["repeat"],
        "expected_evidence_complete": True,
    }


def build_clone(idx: int, rng: random.Random) -> dict:
    """Two patients, same provider, same day, identical procedure pattern."""
    day = _day(idx)
    prv = rng.choice(PROVIDERS)
    loc = rng.choice(LOCATIONS)
    pract = rng.choice(PRACTITIONERS)
    diag_code, _ = rng.choice(ICD10_DIAGNOSES)
    num_lines = rng.randint(2, 3)
    chosen = rng.sample(ICD9_PROCEDURES, num_lines)
    visit_start = day.replace(hour=8)

    def _bundle_for(psn_id: str, suffix: str) -> dict:
        acc  = f"ACC-CLN-{idx}-{suffix}"
        enc  = f"ENC-CLN-{idx}-{suffix}"
        eps  = f"EPS-CLN-{idx}-{suffix}"
        clm  = f"CLM-CLN-{idx}-{suffix}"
        bnd  = f"BND-CLN-{idx}-{suffix}"
        total = 0
        charge_items, lines, procedures, prov = [], [], [], []

        for li, (code, desc, price) in enumerate(chosen, 1):
            ci_id   = f"CI-CLN-{idx}-{suffix}-{li}"
            ln_id   = f"LN-CLN-{idx}-{suffix}-{li}"
            proc_id = f"PROC-CLN-{idx}-{suffix}-{li}"
            svc_at  = visit_start + timedelta(hours=li)
            total  += price
            charge_items.append({
                "account_id": acc, "charge_item_id": ci_id, "code": code,
                "code_system": CODE_SYS_ICD9, "encounter_id": enc,
                "occurred_at": fmt(svc_at), "quantity": "1",
                "total_amount": str(price), "unit_price": str(price),
            })
            lines.append({
                "charge_item_ref": {"resource_id": ci_id, "resource_type": "ChargeItem"},
                "claim_id": clm, "code": code, "code_system": CODE_SYS_ICD9,
                "description": f"Layanan {code}", "line_amount": str(price),
                "line_id": ln_id, "quantity": "1", "service_at": fmt(svc_at),
                "supporting_refs": [{"resource_id": proc_id, "resource_type": "Procedure"}],
                "unit_price": str(price),
            })
            procedures.append({
                "code": code, "code_system": CODE_SYS_ICD9, "encounter_id": enc,
                "location_id": loc, "performed_at": fmt(svc_at), "performer_id": pract,
                "procedure_id": proc_id, "status": "completed",
            })
            prov.append(make_provenance(ln_id, "ClaimLine", day))
            prov.append(make_provenance(proc_id, "Procedure", day))

        submitted = day + timedelta(days=1, hours=8)
        prov.insert(0, make_provenance(clm, "Claim", day))
        prov.insert(1, make_provenance(enc, "Encounter", day))

        return {
            "accounts": [{"account_id": acc, "participant_id": psn_id, "provider_id": prv, "status": "active"}],
            "bundle_id": bnd,
            "charge_items": charge_items,
            "claim": {
                "care_type": "outpatient", "claim_id": clm, "currency": CURRENCY,
                "encounter_id": enc, "episode_id": eps, "participant_id": psn_id,
                "provider_id": prv, "status": "active",
                "submitted_at": fmt(submitted), "total_amount": str(total),
            },
            "conditions": [{
                "code": diag_code, "code_system": CODE_SYS_ICD10,
                "condition_id": f"COND-CLN-{idx}-{suffix}", "encounter_id": enc,
                "onset_at": None, "recorded_at": fmt(visit_start),
                "verification_status": "confirmed",
            }],
            "diagnostics": [], "documents": [],
            "encounters": [{
                "class_code": "AMB", "encounter_id": enc,
                "end_at": fmt(visit_start + timedelta(hours=num_lines + 1)),
                "location_id": loc, "participant_id": psn_id, "provider_id": prv,
                "start_at": fmt(visit_start), "status": "finished",
            }],
            "invoices": [{
                "account_id": acc,
                "charge_item_refs": [{"resource_id": ci["charge_item_id"], "resource_type": "ChargeItem"} for ci in charge_items],
                "invoice_id": f"INV-CLN-{idx}-{suffix}",
                "issued_at": fmt(submitted), "total_amount": str(total),
            }],
            "lines": lines,
            "medications": [],
            "procedures": procedures,
            "provenance": prov,
        }

    baseline_psn = f"PSN-{5000 + idx}"
    target_psn   = f"PSN-{6000 + idx}"
    baseline_bundle = _bundle_for(baseline_psn, "A")
    current_bundle  = _bundle_for(target_psn,  "B")
    bnd = current_bundle["bundle_id"]

    return {
        "scenario": "clone",
        "demo": {"bundle_id": bnd, "description": SCENARIO_DESCRIPTIONS["clone"], "scenario_label": SCENARIO_LABELS["clone"]},
        "history": [baseline_bundle],
        "bundle": current_bundle,
        "expected_reason_codes": EXPECTED_CODES["clone"],
        "expected_evidence_complete": True,
    }


def build_unbundled(idx: int, rng: random.Random) -> dict:
    """Two component procedures billed separately instead of as a bundle code."""
    day = _day(idx)
    psn = f"PSN-{7000 + idx}"
    prv = rng.choice(PROVIDERS)
    loc = rng.choice(LOCATIONS)
    pract = rng.choice(PRACTITIONERS)
    acc = f"ACC-UB-{idx:04d}"
    enc = f"ENC-UB-{idx}"
    eps = f"EPS-UB-{idx}"
    clm = f"CLM-UB-{idx}"
    bnd = f"BND-UB-{idx}"
    diag_code, _ = rng.choice(ICD10_DIAGNOSES)

    # Always use "93.94" + "88.71" as the known unbundling pair
    components = [
        ("93.94", "Terapi Pernapasan",   225_000),
        ("88.71", "USG Kepala dan Leher", 480_000),
    ]
    total = sum(p for _, _, p in components)
    visit_start = day.replace(hour=9)
    submitted = day + timedelta(days=1, hours=8)

    charge_items, lines, procedures, prov = [], [], [], []
    for li, (code, desc, price) in enumerate(components, 1):
        ci_id   = f"CI-UB-{idx}-{li}"
        ln_id   = f"LN-UB-{idx}-{li}"
        proc_id = f"PROC-UB-{idx}-{li}"
        svc_at  = visit_start + timedelta(hours=li - 1)

        charge_items.append({
            "account_id": acc, "charge_item_id": ci_id, "code": code,
            "code_system": CODE_SYS_ICD9, "encounter_id": enc,
            "occurred_at": fmt(svc_at), "quantity": "1",
            "total_amount": str(price), "unit_price": str(price),
        })
        lines.append({
            "charge_item_ref": {"resource_id": ci_id, "resource_type": "ChargeItem"},
            "claim_id": clm, "code": code, "code_system": CODE_SYS_ICD9,
            "description": f"Layanan {code}", "line_amount": str(price),
            "line_id": ln_id, "quantity": "1", "service_at": fmt(svc_at),
            "supporting_refs": [{"resource_id": proc_id, "resource_type": "Procedure"}],
            "unit_price": str(price),
        })
        procedures.append({
            "code": code, "code_system": CODE_SYS_ICD9, "encounter_id": enc,
            "location_id": loc, "performed_at": fmt(svc_at), "performer_id": pract,
            "procedure_id": proc_id, "status": "completed",
        })
        prov.append(make_provenance(ln_id, "ClaimLine", day))
        prov.append(make_provenance(proc_id, "Procedure", day))

    prov.insert(0, make_provenance(clm, "Claim", day))
    prov.insert(1, make_provenance(enc, "Encounter", day))

    bundle = {
        "accounts": [{"account_id": acc, "participant_id": psn, "provider_id": prv, "status": "active"}],
        "bundle_id": bnd,
        "charge_items": charge_items,
        "claim": {
            "care_type": "outpatient", "claim_id": clm, "currency": CURRENCY,
            "encounter_id": enc, "episode_id": eps, "participant_id": psn,
            "provider_id": prv, "status": "active",
            "submitted_at": fmt(submitted), "total_amount": str(total),
        },
        "conditions": [{
            "code": diag_code, "code_system": CODE_SYS_ICD10,
            "condition_id": f"COND-UB-{idx}", "encounter_id": enc,
            "onset_at": None, "recorded_at": fmt(visit_start),
            "verification_status": "confirmed",
        }],
        "diagnostics": [], "documents": [],
        "encounters": [{
            "class_code": "AMB", "encounter_id": enc,
            "end_at": fmt(visit_start + timedelta(hours=3)),
            "location_id": loc, "participant_id": psn, "provider_id": prv,
            "start_at": fmt(visit_start), "status": "finished",
        }],
        "invoices": [{
            "account_id": acc,
            "charge_item_refs": [{"resource_id": ci["charge_item_id"], "resource_type": "ChargeItem"} for ci in charge_items],
            "invoice_id": f"INV-UB-{idx}",
            "issued_at": fmt(submitted), "total_amount": str(total),
        }],
        "lines": lines,
        "medications": [],
        "procedures": procedures,
        "provenance": prov,
    }
    return {
        "scenario": "unbundled",
        "demo": {"bundle_id": bnd, "description": SCENARIO_DESCRIPTIONS["unbundled"], "scenario_label": SCENARIO_LABELS["unbundled"]},
        "history": [],
        "bundle": bundle,
        "expected_reason_codes": EXPECTED_CODES["unbundled"],
        "expected_evidence_complete": True,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

BUILDERS = {
    "clean":     build_clean,
    "phantom":   build_phantom,
    "repeat":    build_repeat,
    "clone":     build_clone,
    "unbundled": build_unbundled,
}

# Distribution: clean 40%, phantom 20%, repeat 15%, clone 15%, unbundled 10%
DISTRIBUTION = (
    ["clean"] * 40
    + ["phantom"] * 20
    + ["repeat"] * 15
    + ["clone"] * 15
    + ["unbundled"] * 10
)


def main(n: int = 250, seed: int = 42) -> int:
    rng = random.Random(seed)
    fixtures_dir = Path(__file__).resolve().parents[1] / "tests" / "fixtures"
    out_path     = fixtures_dir / "bulk_demo.json"
    bundles_dir  = fixtures_dir / "bulk_bundles"

    fixtures_dir.mkdir(parents=True, exist_ok=True)
    bundles_dir.mkdir(parents=True, exist_ok=True)

    fixtures: list[dict] = []
    counts: dict[str, int] = {s: 0 for s in BUILDERS}

    for i in range(n):
        scenario = rng.choice(DISTRIBUTION)
        builder  = BUILDERS[scenario]
        fixture  = builder(i, rng)
        fixtures.append(fixture)
        counts[scenario] += 1

        # Simpan bundle saja (CanonicalBundle) sebagai file individual untuk UI upload
        bundle_only = fixture["bundle"]
        bnd_file = bundles_dir / f"{bundle_only['bundle_id']}.json"
        bnd_file.write_text(json.dumps(bundle_only, indent=2, ensure_ascii=False), encoding="utf-8")

        # Untuk fixture yang punya history (repeat, clone), simpan history bundle juga
        for j, prior in enumerate(fixture.get("history", []), 1):
            prior_file = bundles_dir / f"{prior['bundle_id']}.json"
            prior_file.write_text(json.dumps(prior, indent=2, ensure_ascii=False), encoding="utf-8")

    out_path.write_text(json.dumps(fixtures, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Generated {n} fixtures → {out_path}")
    print(f"Individual bundles     → {bundles_dir}/  ({sum(1 for _ in bundles_dir.iterdir())} files)")
    for s, c in counts.items():
        print(f"  {s:12s}: {c:3d}")
    return 0


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 250
    raise SystemExit(main(n))

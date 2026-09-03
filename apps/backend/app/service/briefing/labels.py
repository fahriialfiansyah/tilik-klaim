"""Working-language names the template needs. Mirrors the frontend's `RESOURCE_LABELS`."""
from __future__ import annotations

RESOURCE_LABELS: dict[str, str] = {
    "Claim": "klaim",
    "ClaimLine": "baris tagihan",
    "Encounter": "kunjungan",
    "Condition": "diagnosis",
    "Procedure": "catatan tindakan",
    "Medication": "catatan obat",
    "Diagnostic": "pemeriksaan penunjang",
    "Document": "catatan klinis",
    "Account": "akun tagihan",
    "ChargeItem": "item biaya",
    "Invoice": "faktur",
    "Episode": "episode",
    "Practitioner": "tenaga kesehatan",
}


def resource_label(resource_type: object) -> str:
    return RESOURCE_LABELS.get(str(resource_type), str(resource_type))

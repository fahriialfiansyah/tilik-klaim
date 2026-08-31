"""Code and narrative vocabulary for the generator.

Small, invented, and deliberately not a real code set. The codes are shaped like ICD/KFA codes
so downstream joins and displays behave realistically, but no clinical meaning attaches to them
and none should be inferred.

Note templates exist so clean encounters read *differently* from one another. That variation is
load-bearing: if every clean note were alike, the clone detector would fire corpus-wide and its
precision measurement would say nothing.
"""
from __future__ import annotations

import hashlib

PROCEDURE_CODES: tuple[str, ...] = (
    "39.95", "88.72", "45.13", "81.51", "86.22",
    "38.93", "99.04", "93.39", "57.94", "34.91",
)

MEDICATION_CODES: tuple[str, ...] = (
    "KFA-1001", "KFA-1002", "KFA-1003", "KFA-1004", "KFA-1005",
    "KFA-1006", "KFA-1007", "KFA-1008",
)

CONDITION_CODES: tuple[str, ...] = (
    "J06.9", "E11.9", "I10", "K29.7", "N39.0",
    "A09", "J18.9", "M54.5", "R50.9", "D64.9",
)

NOTE_TEMPLATES: tuple[str, ...] = (
    "Pasien datang dengan keluhan sejak {days} hari. Pemeriksaan mengarah ke {code}. "
    "Kondisi {finding}. Rencana: {plan}.",
    "Keluhan dirasakan {days} hari terakhir. Hasil pemeriksaan sesuai {code}. "
    "Saat ini {finding}, disarankan {plan}.",
    "Riwayat keluhan {days} hari. Penilaian klinis menunjuk {code}. "
    "Perkembangan {finding}. Tindak lanjut {plan}.",
    "Sejak {days} hari pasien mengeluhkan gejala terkait {code}. "
    "Evaluasi menunjukkan kondisi {finding}; direncanakan {plan}.",
)


def text_hash(text: str) -> str:
    """Digest of a note's text.

    A bundle may carry the hash without the text — `docs/canonical/07_privacy_threat_model.md`
    allows withholding the narrative — so the hash has to be derived the same way everywhere.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


SHINGLE_SIZE = 5
"""Character n-gram width, matching the detector's transparent baseline.

Duplicated here rather than imported: `tilik_data` must not depend on the engine at runtime, or
the generator could see what the detector looks for. The injector uses it only to guarantee a
property of its own output — that a "subtle" copy stays recognisably similar — never to tune
itself against a detector's threshold.
"""


def shingles(text: str) -> frozenset[str]:
    normalised = " ".join(text.lower().split())
    if len(normalised) < SHINGLE_SIZE:
        return frozenset({normalised}) if normalised else frozenset()
    return frozenset(
        normalised[i : i + SHINGLE_SIZE] for i in range(len(normalised) - SHINGLE_SIZE + 1)
    )


def similarity(left: str, right: str) -> float:
    """Character n-gram Jaccard between two notes."""
    a, b = shingles(left), shingles(right)
    union = a | b
    return len(a & b) / len(union) if union else 0.0

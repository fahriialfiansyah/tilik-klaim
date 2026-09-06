"""Working-language text the API composes itself, in both languages it speaks.

Most of what a reviewer reads comes from a catalog: reasons from `tilik_domain.reasons`,
counter-arguments from `tilik_domain.notes`. What is left is the connective text the response
assembles from facts it has just counted — how a band was reached, what a timeline event was,
how many completeness notes lowered certainty. It is small, but it is the text that surrounds
every finding, and leaving it in one language would have produced the worst possible screen:
an English finding framed by Indonesian explanation.

None of it is a catalog entry, because none of it identifies anything. It is rendered from the
response being built and never stored, so it needs no code — only a template per language.
"""
from __future__ import annotations

from tilik_domain.locale import DEFAULT_LOCALE, Locale


def _pick(locale: Locale, indonesian: str, english: str) -> str:
    return english if locale is Locale.EN else indonesian


def no_observed_risk(locale: Locale = DEFAULT_LOCALE) -> str:
    """The queue row for a case where no selected detector fired.

    Never "clean" and never "safe" in either language — `PriorityBand.NO_OBSERVED_RISK` says
    what the engine looked for and did not find, and the system is not entitled to the stronger
    claim. English makes the overreach tempting; this wording refuses it.
    """
    return _pick(
        locale,
        "Tidak ada risiko teramati pada versi mesin ini.",
        "No risk observed at this engine version.",
    )


def band_basis(reason_count: int, locale: Locale = DEFAULT_LOCALE) -> str:
    """How the band was reached: nothing observed, or the strongest of several reasons."""
    if reason_count == 0:
        return _pick(
            locale,
            "Tidak ada sinyal yang teramati pada versi mesin ini.",
            "No signal observed at this engine version.",
        )
    return _pick(
        locale,
        f"{reason_count} alasan teramati; pita mengikuti alasan terkuat.",
        f"{reason_count} {_plural(reason_count, 'reason')} observed; "
        "the band follows the strongest one.",
    )


def cap_similarity_only(locale: Locale = DEFAULT_LOCALE) -> str:
    """Text similarity alone is capped below the top band, by design and by rule."""
    return _pick(
        locale,
        "Kemiripan teks saja tidak pernah mencapai pita tertinggi.",
        "Text similarity alone never reaches the top band.",
    )


def cap_incomplete_bundle(locale: Locale = DEFAULT_LOCALE) -> str:
    return _pick(
        locale,
        "Bundel tidak lengkap menurunkan tingkat keyakinan dan mengarahkan ke "
        "permintaan bukti tambahan.",
        "An incomplete bundle lowered certainty and points toward requesting more evidence.",
    )


def cap_completeness_notes(count: int, locale: Locale = DEFAULT_LOCALE) -> str:
    return _pick(
        locale,
        f"{count} catatan kelengkapan menurunkan tingkat keyakinan.",
        f"{count} completeness {_plural(count, 'note')} lowered certainty.",
    )


def cap_completeness_carried(count: int, locale: Locale = DEFAULT_LOCALE) -> str:
    return _pick(
        locale,
        f"{count} catatan kelengkapan terbawa dari pemasukan berkas.",
        f"{count} completeness {_plural(count, 'note')} carried over from ingest.",
    )


def encounter_event(encounter_id: str, locale: Locale = DEFAULT_LOCALE) -> str:
    return _pick(locale, f"Kunjungan {encounter_id}", f"Encounter {encounter_id}")


def procedure_event(code: str, status: str, locale: Locale = DEFAULT_LOCALE) -> str:
    return _pick(locale, f"Tindakan {code} ({status})", f"Procedure {code} ({status})")


def medication_event(code: str, locale: Locale = DEFAULT_LOCALE) -> str:
    return _pick(locale, f"Obat {code}", f"Medication {code}")


def _plural(count: int, noun: str) -> str:
    """English needs a plural where Indonesian does not. One rule, one place.

    Deliberately naive: every noun this module pluralises takes a bare `-s`. A word that does
    not belongs in a template of its own rather than in a table of exceptions nobody reads.
    """
    return noun if count == 1 else f"{noun}s"

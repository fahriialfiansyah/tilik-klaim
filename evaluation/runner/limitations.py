"""The copy-ready limitations card.

`docs/canonical/06_evaluation_plan.md` requires "one limitations card that can be copied directly
into the proposal". It is the first artifact dropped under deadline pressure and the last one
that should be: a metric quoted without its limits is a claim the data cannot support, and a
judge who finds the gap themselves will discount everything around it.

The demonstrates / does-not-demonstrate rows are carried **verbatim** from the canonical plan's
table. Run-specific caveats are appended beneath them, generated from what the run actually
found — an undefined metric, an absent class, a filtered training set — so the card cannot
quietly stay generic while the numbers change.
"""
from __future__ import annotations

from collections.abc import Sequence

MANDATORY_STATEMENT = (
    "This dataset is synthetic and does not represent JKN prevalence or real provider behavior."
)
"""Required verbatim by the canonical data card. Not paraphrased, not softened."""

DEMONSTRATES: tuple[str, ...] = (
    "Software correctly parses the chosen schema subset",
    "Detectors recover known injected patterns",
    "Hybrid ranking may beat baselines on controlled cases",
    "Evidence references and audit events are reproducible",
    "Prototype latency and workflow can be measured",
)

DOES_NOT_DEMONSTRATE: tuple[str, ...] = (
    "Production compatibility with BPJS/E-Klaim/SATUSEHAT",
    "Real-world JKN fraud accuracy or prevalence",
    "National savings or causal impact",
    "Clinical validity or legal findings",
    "Scale under national production load",
)

IMPACT_MODEL = (
    "No cost saving is claimed. The pilot measurement formula is: expected reviewed value = "
    "reviewed claim amount x observed confirmation rate x recoverable/correctable fraction. "
    "Every factor must be measured or explicitly parameterised in a future authorised pilot; "
    "any scenario figure is an assumption and is reported separately from these results."
)


def as_payload(run_caveats: Sequence[str]) -> dict:
    """The same card as data, so the API serves it without parsing Markdown.

    Both renderings come from one set of values. A machine-readable copy produced by a second
    computation, or scraped back out of the Markdown, is how a page ends up showing limitations
    that no longer match the artifact beside it.
    """
    return {
        "mandatory_statement": MANDATORY_STATEMENT,
        "demonstrates": list(DEMONSTRATES),
        "does_not_demonstrate": list(DOES_NOT_DEMONSTRATE),
        "run_caveats": list(run_caveats),
        "impact_model": IMPACT_MODEL,
    }


def render(run_caveats: Sequence[str]) -> str:
    """Produce the card as Markdown, ready to paste into the deck."""
    demonstrates = "\n".join(f"- {line}" for line in DEMONSTRATES)
    does_not = "\n".join(f"- {line}" for line in DOES_NOT_DEMONSTRATE)
    caveats = "\n".join(f"- {line}" for line in run_caveats) or "- None recorded for this run."
    return f"""# Limitations — TilikKlaim evaluation

> {MANDATORY_STATEMENT}

The system reports risk or anomaly requiring review. It states no finding about any person or
facility, and none could exist: no real person or facility appears in this data.

## What these results demonstrate

{demonstrates}

## What these results do not demonstrate

{does_not}

## Caveats specific to this run

{caveats}

## Impact

{IMPACT_MODEL}
"""


def caveats_for(
    *,
    undefined_metrics: Sequence[str],
    absent_modes: Sequence[str],
    dropped_training_bundles: int,
    unexplained_flag_share: float | None,
    test_bundles: int,
    clean_bundles: int,
) -> tuple[str, ...]:
    """Turn what the run actually found into lines a reader can act on.

    Written in Indonesian: unlike the canonical rows above, these are this project's own words,
    and both consumers read Indonesian — the operator on `/evaluation` and the proposal this
    card is copied into.
    """
    lines: list[str] = [
        (
            f"Diukur pada {test_bundles} berkas klaim yang ditahan, {clean_bundles} di antaranya "
            "tanpa suntikan sama sekali. Proporsi suntikan adalah pilihan rancangan uji, jauh "
            "di atas laju nyata mana pun, dan tidak boleh dikutip sebagai laju nyata."
        ),
    ]
    if absent_modes:
        lines.append(
            f"Tidak ada contoh {', '.join(absent_modes)} pada partisi uji, sehingga "
            "keterpanggilan untuk mode tersebut ditandai tidak terukur, bukan nol."
        )
    if undefined_metrics:
        lines.append(
            "Tidak terdefinisi dan dilaporkan sebagai tidak terukur, bukan nol: "
            f"{', '.join(undefined_metrics)}."
        )
    if dropped_training_bundles:
        lines.append(
            f"{dropped_training_bundles} berkas latih ditahan dari pelatihan karena pesertanya "
            "juga muncul di partisi validasi atau uji. Pembagian yang dipublikasikan "
            "mengelompokkan menurut (peserta, fasilitas, blok waktu), sehingga satu peserta bisa "
            "muncul di dua partisi."
        )
    if unexplained_flag_share is not None and unexplained_flag_share > 0:
        lines.append(
            f"{unexplained_flag_share:.1%} penandaan hibrida muncul dari skor model tanpa alasan "
            "aturan di belakangnya. Kasus seperti itu tidak punya penjelasan yang bisa dibaca "
            "peninjau, dan dihitung di sini alih-alih disembunyikan."
        )
    lines.append(
        "Catatan klinis dibuat dari segelintir templat, sehingga deteksi salinan hampir pasti "
        "lebih mudah di sini daripada di lapangan."
    )
    lines.append(
        "Nilai rupiah bersifat ilustratif dan dipilih agar aritmetika baris dapat diperiksa. "
        "Tidak satu pun menyerupai tarif nyata dan tidak boleh disajikan sebagai tarif."
    )
    return tuple(lines)

"""Counter-evidence notes — the arguments *against* each reason, catalogued.

Every reason the engine raises ships with the honest alternative readings of the same facts:
shared templates explain near-identical notes, staged care explains an episode split across
claims, a resubmission after a correction explains an identical fingerprint. The reviewer must
see those on the same screen as the signal, and `docs/canonical/07_privacy_threat_model.md`
makes at least one of them mandatory on the most accusatory reason the engine can emit.

They used to be written as literal sentences at the point the rule fired, which was fine while
the product spoke one language and impossible the moment it spoke two: the text was composed
during screening and frozen into the stored case, so an English reader would have been handed
Indonesian arguments beside English findings.

So a note is now a **code plus its parameters**, exactly like a reason is a `ReasonCode`. The
rule decides *which* argument applies and supplies the facts it needs; the language is chosen
at the edge of the API, when someone reads it. Stored cases keep their Indonesian text in
`note_id` and are still readable — see `render` — but every note raised from here on can be
read in either language without re-screening anything.
"""
from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from tilik_domain.locale import DEFAULT_LOCALE, Locale


class NoteCode(StrEnum):
    """Stable identifiers for counter-evidence notes. Never renumbered."""

    ENTERED_IN_ERROR_MAY_BE_CORRECTION = "ENTERED_IN_ERROR_MAY_BE_CORRECTION"
    BUNDLE_HOLDS_ONLY_WHAT_WAS_SENT = "BUNDLE_HOLDS_ONLY_WHAT_WAS_SENT"
    UNRESOLVABLE_REFERENCES_PRESENT = "UNRESOLVABLE_REFERENCES_PRESENT"
    NO_ENCOUNTER_DATA_AT_ALL = "NO_ENCOUNTER_DATA_AT_ALL"
    SHARED_TEMPLATES_EXPLAIN_SIMILARITY = "SHARED_TEMPLATES_EXPLAIN_SIMILARITY"
    RECURRING_COMPLAINT_EXPLAINS_SIMILARITY = "RECURRING_COMPLAINT_EXPLAINS_SIMILARITY"
    STAGED_CARE_LOOKS_THE_SAME = "STAGED_CARE_LOOKS_THE_SAME"
    CLAIMS_ALREADY_GROUPED_BY_EPISODE = "CLAIMS_ALREADY_GROUPED_BY_EPISODE"
    RESUBMISSION_AFTER_CORRECTION = "RESUBMISSION_AFTER_CORRECTION"
    CLAIMS_SEPARATED_BY_DAYS = "CLAIMS_SEPARATED_BY_DAYS"
    DIFFERING_FIELDS_SUGGEST_SEPARATE_SERVICES = "DIFFERING_FIELDS_SUGGEST_SEPARATE_SERVICES"


class NoteDefinition(BaseModel):
    """One catalog entry: the same argument in each language we speak."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    code: NoteCode
    template_id: str
    """Indonesian. `str.format` placeholders only, and only for facts the rule supplies."""
    template_en: str
    """English. Must take exactly the same placeholders — a note that needs a fact in one
    language and not the other is two different arguments wearing one code."""

    def render(self, locale: Locale = DEFAULT_LOCALE, **params: object) -> str:
        template = self.template_en if locale is Locale.EN else self.template_id
        try:
            return template.format(**params)
        except (KeyError, IndexError):
            # A note missing a parameter is a bug in the rule that raised it, but a reviewer
            # losing the counter-argument entirely is the worse failure: an unfilled template
            # still names the alternative reading. `test_notes` guards the real contract.
            return template


def _build_catalog() -> dict[NoteCode, NoteDefinition]:
    definitions = (
        NoteDefinition(
            code=NoteCode.ENTERED_IN_ERROR_MAY_BE_CORRECTION,
            template_id=(
                "Penandaan keliru-input bisa berarti koreksi administratif, "
                "bukan layanan yang tidak diberikan."
            ),
            template_en=(
                "An entered-in-error marking can mean an administrative correction, "
                "not a service that was never delivered."
            ),
        ),
        NoteDefinition(
            code=NoteCode.BUNDLE_HOLDS_ONLY_WHAT_WAS_SENT,
            template_id=(
                "Bundel ini hanya memuat bukti yang ikut terkirim. Tidak ditemukannya "
                "catatan di sini bukan bukti bahwa layanan tidak diberikan — catatan "
                "bisa berada di berkas fisik atau sistem lain."
            ),
            template_en=(
                "This bundle holds only the evidence that was sent with it. Finding no "
                "record here is not evidence that the service was not delivered — records "
                "may sit in paper files or another system."
            ),
        ),
        NoteDefinition(
            code=NoteCode.UNRESOLVABLE_REFERENCES_PRESENT,
            template_id=(
                "Bundel ini memuat rujukan yang tidak dapat diselesaikan, "
                "sehingga bukti pendukung mungkin ada tetapi tidak ikut terkirim."
            ),
            template_en=(
                "This bundle contains references that could not be resolved, so supporting "
                "evidence may exist without having been sent."
            ),
        ),
        NoteDefinition(
            code=NoteCode.NO_ENCOUNTER_DATA_AT_ALL,
            template_id=(
                "Bundel tidak memuat data kunjungan, sehingga bukti klinis "
                "tidak dapat ditelusuri sama sekali."
            ),
            template_en=(
                "The bundle carries no encounter data, so clinical evidence could not be "
                "traced at all."
            ),
        ),
        NoteDefinition(
            code=NoteCode.SHARED_TEMPLATES_EXPLAIN_SIMILARITY,
            template_id=(
                "Formulir dan templat catatan yang dipakai bersama menghasilkan "
                "kemiripan tinggi tanpa ada yang disalin."
            ),
            template_en=(
                "Shared forms and note templates produce high similarity without anything "
                "having been copied."
            ),
        ),
        NoteDefinition(
            code=NoteCode.RECURRING_COMPLAINT_EXPLAINS_SIMILARITY,
            template_id=(
                "Keluhan yang berulang pada pasien yang sama wajar menghasilkan "
                "catatan yang hampir sama."
            ),
            template_en=(
                "A recurring complaint in the same patient reasonably produces nearly "
                "identical notes."
            ),
        ),
        NoteDefinition(
            code=NoteCode.STAGED_CARE_LOOKS_THE_SAME,
            template_id=(
                "Layanan bertahap yang direncanakan juga tampak seperti ini: satu episode, "
                "beberapa klaim berdekatan, dengan tindakan yang berbeda-beda."
            ),
            template_en=(
                "Planned staged care looks like this too: one episode, several nearby "
                "claims, each with different procedures."
            ),
        ),
        NoteDefinition(
            code=NoteCode.CLAIMS_ALREADY_GROUPED_BY_EPISODE,
            template_id=(
                "Klaim-klaim ini memang dikelompokkan pada episode {episode_id}, "
                "sehingga keterkaitannya sudah tercatat dan bukan temuan tersembunyi."
            ),
            template_en=(
                "These claims are in fact grouped under episode {episode_id}, so their "
                "relationship is already on record rather than a hidden finding."
            ),
        ),
        NoteDefinition(
            code=NoteCode.RESUBMISSION_AFTER_CORRECTION,
            template_id=(
                "Sidik identik juga muncul saat klaim dikirim ulang "
                "setelah koreksi administratif."
            ),
            template_en=(
                "An identical fingerprint also appears when a claim is resubmitted after an "
                "administrative correction."
            ),
        ),
        NoteDefinition(
            code=NoteCode.CLAIMS_SEPARATED_BY_DAYS,
            template_id=(
                "Kedua klaim terpisah {days} hari, jarak yang lazim "
                "untuk kunjungan ulang yang sah."
            ),
            template_en=(
                "The two claims are {days} days apart, a normal interval for a legitimate "
                "follow-up visit."
            ),
        ),
        NoteDefinition(
            code=NoteCode.DIFFERING_FIELDS_SUGGEST_SEPARATE_SERVICES,
            template_id=(
                "Bidang berikut berbeda antara kedua klaim, sehingga keduanya "
                "mungkin memang layanan terpisah: {fields}."
            ),
            template_en=(
                "The following fields differ between the two claims, so they may genuinely "
                "be separate services: {fields}."
            ),
        ),
    )
    return {definition.code: definition for definition in definitions}


NOTE_CATALOG: dict[NoteCode, NoteDefinition] = _build_catalog()


def definition_for(code: NoteCode) -> NoteDefinition:
    """Look up a note definition. Raises when a code is not catalogued."""
    try:
        return NOTE_CATALOG[code]
    except KeyError as exc:  # pragma: no cover - guarded by test_notes
        raise KeyError(f"Note code {code!r} is not in the catalog") from exc


def render(
    code: NoteCode | None,
    fallback: str,
    locale: Locale = DEFAULT_LOCALE,
    **params: object,
) -> str:
    """Render a note, falling back to text that was already composed.

    `fallback` is the stored `note_id` sentence. Cases screened before this catalog existed
    carry no code, and they must stay readable — dropping their counter-evidence would strip
    the argument against a reason from every case already in the queue. Those rows read in
    Indonesian whichever locale is asked for, which is a visible gap rather than a silent one.
    """
    if code is None:
        return fallback
    return definition_for(code).render(locale, **params)

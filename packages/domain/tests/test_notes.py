"""Counter-evidence catalog invariants.

Counter-evidence is not decoration: `docs/canonical/01_product_decision.md` makes showing the
argument against a signal part of the product. These tests guard the properties that keep it
that way once the same argument has to exist in two languages.
"""
from __future__ import annotations

import re
import string

import pytest

from tilik_domain.locale import Locale
from tilik_domain.notes import NOTE_CATALOG, NoteCode, definition_for, render


def _placeholders(template: str) -> set[str]:
    return {
        field for _, field, _, _ in string.Formatter().parse(template) if field is not None
    }


def test_every_note_code_is_catalogued() -> None:
    """A code a stored hit can carry but the API cannot render is a blank counter-argument."""
    assert set(NOTE_CATALOG) == set(NoteCode)


@pytest.mark.parametrize("code", list(NoteCode))
def test_both_languages_take_exactly_the_same_facts(code: NoteCode) -> None:
    """A note needing a fact in one language and not the other is two arguments, one code."""
    definition = definition_for(code)
    assert _placeholders(definition.template_id) == _placeholders(definition.template_en)


@pytest.mark.parametrize("code", list(NoteCode))
def test_every_note_is_a_sentence_in_both_languages(code: NoteCode) -> None:
    definition = definition_for(code)
    for template in (definition.template_id, definition.template_en):
        assert template.strip().endswith("."), f"{code} is not a sentence"


@pytest.mark.parametrize("code", list(NoteCode))
def test_no_note_was_left_untranslated(code: NoteCode) -> None:
    definition = definition_for(code)
    assert definition.template_id != definition.template_en, f"{code} was never translated"


def test_a_note_renders_the_facts_the_rule_supplied() -> None:
    rendered = render(NoteCode.CLAIMS_SEPARATED_BY_DAYS, "unused", Locale.EN, days=4)
    assert "4 days apart" in rendered

    indonesian = render(NoteCode.CLAIMS_SEPARATED_BY_DAYS, "unused", Locale.ID, days=4)
    assert "terpisah 4 hari" in indonesian


def test_a_record_with_no_code_keeps_its_stored_sentence() -> None:
    """Cases screened before the catalog existed must not lose their counter-argument.

    Dropping it would strip the argument against a reason from every case already in the queue
    — the reader would see the signal with nothing weighing against it, which is precisely the
    screen the product exists to avoid.
    """
    assert render(None, "kalimat lama", Locale.EN) == "kalimat lama"


def test_a_missing_fact_still_names_the_alternative_reading() -> None:
    """A rule that forgot a parameter is a bug; a reviewer losing the argument is worse."""
    rendered = render(NoteCode.CLAIMS_SEPARATED_BY_DAYS, "unused", Locale.EN)
    assert "follow-up visit" in rendered


@pytest.mark.parametrize("code", list(NoteCode))
def test_no_note_accuses_anyone(code: NoteCode) -> None:
    """These are the arguments *for* the facility. They least of all may read as accusations."""
    definition = definition_for(code)
    forbidden = ("fraud", "penipuan", "kecurangan", "fraudulent", "proven", "terbukti")
    for template in (definition.template_id, definition.template_en):
        lowered = template.lower()
        for term in forbidden:
            assert term not in lowered, f"{code} uses accusatory wording: {term!r}"


def test_unknown_note_code_raises() -> None:
    with pytest.raises(KeyError):
        definition_for("NOT_A_REAL_CODE")  # type: ignore[arg-type]


def test_templates_use_named_facts_not_positions() -> None:
    """Positional slots reorder differently per language and silently swap two facts."""
    for definition in NOTE_CATALOG.values():
        for template in (definition.template_id, definition.template_en):
            assert not re.search(r"\{\d*\}", template), f"{definition.code} uses a positional slot"

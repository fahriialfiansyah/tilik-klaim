"""The assistant's names for things are the screen's names for things.

`wording.py` mirrors mode, band, state and resource labels from the web app's locale files, so a
template answer and the page it sits on never call one thing two names. This reads those files
and fails the moment either side drifts — the same discipline `export_access_matrix.py` follows
for the role matrix.

It also checks the reverse dependency: every suggestion chip the page offers must be a question
the template recognises, or clicking one on an offline demo would answer "I don't recognise this".
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from tilik_domain.locale import Locale

from app.dto.assistant import AnswerIntent, RefusalTopic, ScopeKind
from app.service.assistant import wording
from app.service.assistant.intents import classify
from app.service.assistant.validation import forbidden_term

WEB_LOCALES = Path(__file__).resolve().parents[3] / "apps" / "web" / "src" / "locales"


def web(locale: Locale, namespace: str) -> dict:
    return json.loads((WEB_LOCALES / locale.value / f"{namespace}.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("locale", list(Locale))
def test_mode_band_and_state_names_match_the_screen(locale: Locale) -> None:
    review = web(locale, "review")
    assert {str(k): v for k, v in wording.MODE_LABELS[locale].items()} == review["mode"]
    assert {str(k): v for k, v in wording.BAND_LABELS[locale].items()} == review["band"]
    for state, label in wording.STATE_LABELS[locale].items():
        assert review["state"][str(state)] == label, state


@pytest.mark.parametrize("locale", list(Locale))
def test_every_suggestion_on_the_page_is_a_question_the_template_answers(locale: Locale) -> None:
    suggestions = web(locale, "assistant")["suggestions"]
    for scope_key, scope in (("queue", ScopeKind.QUEUE), ("case", ScopeKind.CASE)):
        for question in suggestions[scope_key].values():
            reading = classify(question, scope)
            assert reading.intent not in (
                AnswerIntent.UNRECOGNISED,
                AnswerIntent.OUT_OF_SCOPE,
            ), question


@pytest.mark.parametrize("locale", list(Locale))
def test_the_fixed_notes_pass_the_lexicon(locale: Locale) -> None:
    for text in (
        wording.uncertainty_queue(locale),
        wording.uncertainty_case(locale),
        wording.uncertainty_notice(locale),
        wording.template_caveat(locale),
        wording.help_notice(locale, in_case=True),
        wording.help_notice(locale, in_case=False),
    ):
        assert forbidden_term(text) is None, text


@pytest.mark.parametrize("topic", list(RefusalTopic))
def test_every_refusal_has_copy_in_both_languages(topic: RefusalTopic) -> None:
    assert wording.refusal(topic, Locale.ID) != wording.refusal(topic, Locale.EN)
    assert wording.refusal(topic, Locale.ID).strip()

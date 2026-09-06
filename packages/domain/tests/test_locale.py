"""Language negotiation.

The header is the only thing that decides which language a reader gets, so the rules it follows
are worth stating as tests rather than trusting to a one-line parser.
"""
from __future__ import annotations

import pytest

from tilik_domain.locale import DEFAULT_LOCALE, Locale, negotiate


def test_the_default_is_the_working_language() -> None:
    """Indonesian is what the product is written in, not a fallback of last resort."""
    assert DEFAULT_LOCALE is Locale.ID


@pytest.mark.parametrize("header", [None, "", "fr", "de-DE,de;q=0.9", "*", "   "])
def test_anything_we_cannot_honour_falls_back_to_the_working_language(header: str | None) -> None:
    """Including `*`: no preference means the working language, not whatever sorts first."""
    assert negotiate(header) is DEFAULT_LOCALE


@pytest.mark.parametrize("header", ["en", "en-GB", "en-US,en;q=0.9", "EN-au"])
def test_any_english_variant_resolves_to_english(header: str) -> None:
    """We have one English. Handing a British reviewer Indonesian would help nobody."""
    assert negotiate(header) is Locale.EN


def test_weights_decide_when_both_languages_are_offered() -> None:
    assert negotiate("en;q=0.4,id;q=0.9") is Locale.ID
    assert negotiate("id;q=0.4,en;q=0.9") is Locale.EN


def test_a_language_refused_with_q0_is_never_selected() -> None:
    """`q=0` is an explicit refusal, not a weak preference."""
    assert negotiate("en;q=0,fr") is DEFAULT_LOCALE


def test_an_unweighted_tag_outranks_a_weighted_one() -> None:
    """Absent `q` means 1.0, which is the maximum — RFC 9110 § 12.4.2."""
    assert negotiate("id;q=0.8,en") is Locale.EN


def test_a_malformed_weight_does_not_discard_the_language() -> None:
    """The client still named a language; only the weight is unreadable."""
    assert negotiate("en;q=banana") is Locale.EN

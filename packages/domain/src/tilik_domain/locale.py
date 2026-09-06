"""The languages the product speaks, and how a request picks one.

Indonesian is the **working language**: it is what the reviewers who use this tool actually
speak, what `docs/canonical/` is written in, and what every stored screening result already
holds. English is a second rendering of the same catalog — never a second catalog.

That distinction is the whole design. A reason is raised once, stored once, and keyed by its
`ReasonCode`; the locale only decides which sentence that code is rendered as at the edge of
the API. Nothing about *which* reasons fire, or *what* evidence they carry, can differ between
languages, because a case that read differently in English would be a different case.

Indonesian is also the fallback for every ambiguity — a missing header, an unparseable one, a
language we do not speak. A reviewer who gets the working language when we are unsure has lost
nothing; one who gets a half-translated screen has.
"""
from __future__ import annotations

from enum import StrEnum


class Locale(StrEnum):
    """A language the API can render its catalog text in."""

    ID = "id"
    EN = "en"


DEFAULT_LOCALE = Locale.ID
"""Indonesian. See the module docstring: the working language is never a fallback of last
resort, it is the default the product is written in."""


def _quality(part: str) -> float:
    """The `q=` weight of one Accept-Language entry. Absent means 1.0, per RFC 9110 § 12.4.2."""
    for parameter in part.split(";")[1:]:
        name, _, value = parameter.strip().partition("=")
        if name.strip().lower() == "q":
            try:
                return float(value)
            except ValueError:
                # A malformed weight is not a reason to drop the tag — the browser still
                # named a language. Treating it as unweighted keeps the preference visible.
                return 1.0
    return 1.0


def negotiate(header: str | None) -> Locale:
    """Pick a locale from an `Accept-Language` header.

    Matches on the primary subtag only, so `en-GB`, `en-US` and `en` all resolve to English —
    we have one English, and refusing a regional variant would hand a British reviewer
    Indonesian for no reason. Entries are considered in weight order, and `q=0` means the
    client explicitly refused that language, so it is never selected.

    Anything we cannot honour falls through to `DEFAULT_LOCALE`, including `*`: a client with
    no preference gets the working language rather than whichever tag happens to sort first.
    """
    if not header:
        return DEFAULT_LOCALE

    ranked = sorted(
        (
            (_quality(part), part.split(";")[0].strip().lower())
            for part in header.split(",")
            if part.strip()
        ),
        key=lambda entry: entry[0],
        reverse=True,
    )
    for weight, tag in ranked:
        if weight <= 0:
            continue
        primary = tag.partition("-")[0]
        if primary in set(Locale):
            return Locale(primary)
    return DEFAULT_LOCALE

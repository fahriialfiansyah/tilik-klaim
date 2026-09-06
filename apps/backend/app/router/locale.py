"""Which language a response is rendered in, resolved once per request.

The locale reaches every endpoint the standard way — `Accept-Language`, which the browser
already sends and which `tilik_domain.locale.negotiate` reduces to one of the two languages we
speak. There is no `?lang=` parameter and no per-user setting on the server: language is a
property of who is *reading* a response, not of the case being read, and putting it in the URL
would make two URLs for one case and give the cache two answers to the same question.

Nothing about the screening result changes with it. Reasons are stored by code and rendered
here at the edge, so an English reader and an Indonesian reader looking at the same case see
the same findings, the same evidence, and the same band — in their own language.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header
from tilik_domain.locale import DEFAULT_LOCALE, Locale, negotiate

AcceptLanguage = Annotated[str | None, Header(alias="Accept-Language")]


def request_locale(accept_language: AcceptLanguage = None) -> Locale:
    """The locale for this request, defaulting to the working language."""
    return negotiate(accept_language)


RequestLocale = Annotated[Locale, Depends(request_locale)]
"""Inject into any endpoint that returns catalog text.

Endpoints that return only identifiers, numbers, and timestamps do not need it — adding it
there would advertise a choice the response cannot honour.
"""

__all__ = ["AcceptLanguage", "DEFAULT_LOCALE", "Locale", "RequestLocale", "request_locale"]

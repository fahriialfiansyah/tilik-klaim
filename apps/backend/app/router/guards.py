"""One capability check, shared by every router that restricts anything.

Duplicating the check in five routers is how the sixth one gets forgotten, and a role matrix
enforced in four of five places is not a role matrix. `app/service/access.py` holds the table;
this module is the two lines each endpoint needs to consult it.

The role arrives in `X-Actor-Role`, which is forgeable — see ADR-0006 § 4 and the module
docstring of `app/router/users.py`. Refusing what the *claimed* role may not do is what makes
separation of duties a behaviour of this system; verifying the claim is a production requirement
this prototype does not meet and does not say it meets.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import Header, Response

from app.errors import ErrorCode, ErrorResponse
from app.service.access import CODE_FOR_CAPABILITY, Capability, has_capability, refusal_detail

DEFAULT_ROLE = "reviewer"
"""What a request with no role header is treated as.

A compatibility choice, not a security one: existing callers send no header and the seven frozen
endpoints' documented behaviour depends on this default. The header is forgeable either way.
"""

ActorRole = Annotated[str, Header(alias="X-Actor-Role")]
ActorId = Annotated[str | None, Header(alias="X-Actor-Id")]


def error_response(code: ErrorCode, detail: str) -> Response:
    """The one error envelope, rendered by hand so the status follows the code."""
    envelope = ErrorResponse(code=code, detail=detail)
    return Response(
        content=envelope.model_dump_json(),
        status_code=envelope.http_status,
        media_type="application/json",
    )


def refuse_without(role: str, capability: Capability) -> Response | None:
    """`None` when the role may act; a ready-to-return refusal when it may not."""
    if has_capability(role, capability):
        return None
    return error_response(CODE_FOR_CAPABILITY[capability], refusal_detail(role, capability))

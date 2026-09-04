"""Who may do what — one table, consulted by every endpoint that restricts anything.

`docs/canonical/decisions/ADR-0006-three-roles-and-simulated-login.md` § 2 is the authority for
the matrix below; this module is that matrix in executable form. It extends the two frozensets
that already lived in `app/service/disposition.py` rather than introducing a second mechanism
beside them — two places to ask "may this role do this" is how the two answers start to differ.

**The role arrives in a forgeable header.** `X-Actor-Role` can be set to anything by anyone with
`curl`, and nothing here verifies the caller is who it says. That is documented rather than
hidden (ADR-0006 § 4): production enforcement means a Bearer identity checked before the role is
trusted, and it is a stated future requirement, not a shipped feature. What this module does is
make the refusals real and consistent, so the separation of duties the threat model names is a
behaviour of the system and not only a paragraph about it.
"""
from __future__ import annotations

from enum import StrEnum

from app.errors import ErrorCode


class Role(StrEnum):
    """The three roles. There is no fourth, and adding one needs a new ADR.

    `auditor` was retired by ADR-0006: its capability set was identical to `senior_reviewer`'s,
    so keeping both names preserved an ambiguity with no behaviour behind it.
    """

    REVIEWER = "reviewer"
    SENIOR_REVIEWER = "senior_reviewer"
    ADMIN = "admin"


class Capability(StrEnum):
    """One row of the ADR-0006 § 2 matrix each. Named for the act, not for the endpoint."""

    READ_CASES = "READ_CASES"
    RECORD_DISPOSITION = "RECORD_DISPOSITION"
    REOPEN_DISMISSED_CASE = "REOPEN_DISMISSED_CASE"
    READ_CASE_AUDIT = "READ_CASE_AUDIT"
    INGEST_BUNDLE = "INGEST_BUNDLE"
    READ_EVALUATION = "READ_EVALUATION"
    REQUEST_BRIEFING = "REQUEST_BRIEFING"
    MANAGE_USERS = "MANAGE_USERS"
    READ_USER_AUDIT = "READ_USER_AUDIT"


CAPABILITIES: dict[Role, frozenset[Capability]] = {
    Role.REVIEWER: frozenset(
        {
            Capability.READ_CASES,
            Capability.RECORD_DISPOSITION,
            Capability.READ_CASE_AUDIT,
            Capability.INGEST_BUNDLE,
            Capability.READ_EVALUATION,
            Capability.REQUEST_BRIEFING,
        }
    ),
    Role.SENIOR_REVIEWER: frozenset(
        {
            Capability.READ_CASES,
            Capability.RECORD_DISPOSITION,
            Capability.REOPEN_DISMISSED_CASE,
            Capability.READ_CASE_AUDIT,
            Capability.INGEST_BUNDLE,
            Capability.READ_EVALUATION,
            Capability.REQUEST_BRIEFING,
        }
    ),
    # Deliberately disjoint from the reviewer set. An administrator who could also open a case
    # would be the counterexample to the control this matrix exists to demonstrate.
    Role.ADMIN: frozenset({Capability.MANAGE_USERS, Capability.READ_USER_AUDIT}),
}
"""The matrix. Every entry is asserted by `tests/test_access.py` against every endpoint."""


def parse_role(raw: str) -> Role | None:
    """The header value as a `Role`, or `None` when it names no role this system has.

    An unknown role is not silently downgraded to `reviewer`: a caller claiming `superuser`
    has claimed something untrue, and answering it as if it had said `reviewer` would hide that.
    """
    try:
        return Role(raw)
    except ValueError:
        return None


def has_capability(raw_role: str, capability: Capability) -> bool:
    role = parse_role(raw_role)
    if role is None:
        return False
    return capability in CAPABILITIES[role]


CODE_FOR_CAPABILITY: dict[Capability, ErrorCode] = {
    Capability.READ_CASES: ErrorCode.CASE_ACCESS_FORBIDDEN,
    Capability.RECORD_DISPOSITION: ErrorCode.CASE_ACCESS_FORBIDDEN,
    Capability.REOPEN_DISMISSED_CASE: ErrorCode.CASE_REOPEN_FORBIDDEN,
    Capability.READ_CASE_AUDIT: ErrorCode.AUDIT_FORBIDDEN,
    Capability.INGEST_BUNDLE: ErrorCode.CASE_ACCESS_FORBIDDEN,
    Capability.READ_EVALUATION: ErrorCode.CASE_ACCESS_FORBIDDEN,
    Capability.REQUEST_BRIEFING: ErrorCode.CASE_ACCESS_FORBIDDEN,
    Capability.MANAGE_USERS: ErrorCode.USER_MANAGEMENT_FORBIDDEN,
    Capability.READ_USER_AUDIT: ErrorCode.USER_MANAGEMENT_FORBIDDEN,
}
"""Which stable code a refusal carries. The UI branches on these, so they never change meaning."""


def refusal_detail(raw_role: str, capability: Capability) -> str:
    """A sentence naming the role and what it may not do. Never leaks anything else."""
    return f"Role {raw_role!r} may not perform {capability}."

"""The three synthetic staff, defined once and used by seeding, demo reset, and the tests.

Fixed at three by ADR-0006 § 7: there is no create and no delete, so this list *is* the roster.

**These passcodes are not secrets, by construction.** They are printed on the login screen
beside the account they belong to, and the whole sign-in is persona selection with a
credential-shaped interface (ADR-0006 § 3). Nothing here is a credential, so nothing here
belongs in `.env` — a real credential would, and `.env.example` documents its name with an
empty value.

Emails use the RFC 2606 reserved `.example` TLD so no address can ever resolve, the same
discipline the vLLM tests apply with `gateway.invalid`.
"""
from __future__ import annotations

from app.service.access import Role
from app.store.users import UserRecord, UserStore, now

SEEDED_STAFF: tuple[tuple[str, str, str, str, Role, str], ...] = (
    (
        "usr_sari_wulandari",
        "PTG-01",
        "Sari Wulandari",
        "sari.wulandari@rsud-demo.example",
        Role.REVIEWER,
        "demo-reviewer-2026",
    ),
    (
        "usr_budi_santoso",
        "PTG-02",
        "Budi Santoso",
        "budi.santoso@rsud-demo.example",
        Role.SENIOR_REVIEWER,
        "demo-senior-2026",
    ),
    (
        "usr_rina_hartati",
        "PTG-03",
        "Rina Hartati",
        "rina.hartati@rsud-demo.example",
        Role.ADMIN,
        "demo-admin-2026",
    ),
)
"""`(user_id, staff_token, full_name, email, role, demo_passcode)` — the whole roster."""


def seed_users(store: UserStore) -> tuple[UserRecord, ...]:
    """Write the three accounts, active and never signed in.

    Idempotent by construction: ids are natural keys, so re-seeding restores a roster a demo
    left half-toggled rather than adding a second copy of it.
    """
    stamp = now()
    records = tuple(
        UserRecord(
            user_id=user_id,
            staff_token=staff_token,
            full_name=full_name,
            email=email,
            role=role,
            demo_passcode=passcode,
            is_active=True,
            last_signed_in_at=None,
            created_at=stamp,
            updated_at=stamp,
        )
        for user_id, staff_token, full_name, email, role, passcode in SEEDED_STAFF
    )
    for record in records:
        store.save(record)
    return records

"""Sign in as a persona, and manage the synthetic roster.

Two acts live here and neither is authentication. `start_session` checks a passcode that is
printed on the login screen beside the account it belongs to — it selects which persona the
prototype is being driven as, and ADR-0006 § 3 says so in the words this docstring is quoting.

The management side is narrow by decision: change a role, or flip an active flag. No create, no
delete, no passcode reset. Each change appends an event carrying actor, target, and both values,
and the event is never edited — a history of who was granted what is worth no more than a case
history if it can be rewritten afterwards.

**An administrator may not change their own role or deactivate themselves.** Locking the only
administrator out of the only administrative page is a defect, not a decision the server should
faithfully carry out, so it is refused here rather than merely hidden in the UI.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.errors import ErrorCode
from app.service.access import Role
from app.store.users import UserAuditRecord, UserRecord, UserStore, new_user_event_id, now

ROLE_CHANGED = "USER_ROLE_CHANGED"
DEACTIVATED = "USER_DEACTIVATED"
REACTIVATED = "USER_REACTIVATED"


@dataclass(frozen=True)
class UserActionRefused(Exception):
    """The change was not applied, and no partial event was written."""

    code: ErrorCode
    detail: str

    def __str__(self) -> str:
        return self.detail


@dataclass(frozen=True)
class UserUpdateOutcome:
    user: UserRecord
    events: tuple[UserAuditRecord, ...]


def start_session(email: str, passcode: str, *, store: UserStore) -> UserRecord:
    """Select a persona, or refuse and say why in a sentence the login page can show.

    A wrong passcode and an unknown email answer with the *same* code and the same sentence.
    Distinguishing them would tell a caller which addresses exist, and there is no reason to —
    the three that do are printed on the page.

    A deactivated account is different, and is told apart deliberately: the person typed the
    right credentials, and "salah" would send them looking for a typo that is not there.
    """
    found = store.find_by_email(email)
    if found is None or found.demo_passcode != passcode:
        raise UserActionRefused(
            ErrorCode.SESSION_INVALID_CREDENTIALS,
            "Email atau kode demo tidak cocok. Ketiga akun contoh tertera di halaman ini.",
        )
    if not found.is_active:
        raise UserActionRefused(
            ErrorCode.SESSION_ACCOUNT_DEACTIVATED,
            (
                f"Akun {found.staff_token} dinonaktifkan, jadi tidak dapat masuk. "
                "Administrator dapat mengaktifkannya kembali di Manajemen Pengguna."
            ),
        )

    signed_in = found.model_copy(update={"last_signed_in_at": now()})
    store.save(signed_in)
    return signed_in


def update_user(
    target_id: str,
    *,
    role: Role | None,
    is_active: bool | None,
    actor: UserRecord,
    store: UserStore,
) -> UserUpdateOutcome:
    """Apply a role change, an active-flag change, or both — appending one event per field."""
    if role is None and is_active is None:
        raise UserActionRefused(
            ErrorCode.USER_NO_CHANGE_REQUESTED,
            "Tidak ada perubahan yang diminta.",
        )

    target = store.get(target_id)
    if target is None:
        raise UserActionRefused(ErrorCode.USER_NOT_FOUND, f"Tidak ada pengguna {target_id}.")

    _refuse_self_modification(target, actor, role=role, is_active=is_active)

    updated = target
    events: list[UserAuditRecord] = []

    if role is not None and role is not target.role:
        events.append(_event(ROLE_CHANGED, actor, target, "role", target.role, role))
        updated = updated.model_copy(update={"role": role})

    if is_active is not None and is_active != target.is_active:
        kind = REACTIVATED if is_active else DEACTIVATED
        before, after = _flag(target.is_active), _flag(is_active)
        events.append(_event(kind, actor, target, "is_active", before, after))
        updated = updated.model_copy(update={"is_active": is_active})

    if not events:
        raise UserActionRefused(
            ErrorCode.USER_NO_CHANGE_REQUESTED,
            "Nilai yang dikirim sama dengan nilai saat ini; tidak ada yang dicatat.",
        )

    updated = updated.model_copy(update={"updated_at": now()})
    store.save(updated)
    for event in events:
        store.append_event(event)
    return UserUpdateOutcome(user=updated, events=tuple(events))


def _refuse_self_modification(
    target: UserRecord, actor: UserRecord, *, role: Role | None, is_active: bool | None
) -> None:
    if target.user_id != actor.user_id:
        return
    if role is not None and role is not target.role:
        raise UserActionRefused(
            ErrorCode.USER_SELF_MODIFICATION_REFUSED,
            (
                "Anda tidak dapat mengubah peran akun Anda sendiri. Perubahan ini akan "
                "mengunci Anda keluar dari halaman ini, dan tidak ada administrator lain "
                "yang dapat mengembalikannya."
            ),
        )
    if is_active is False:
        raise UserActionRefused(
            ErrorCode.USER_SELF_MODIFICATION_REFUSED,
            "Anda tidak dapat menonaktifkan akun Anda sendiri.",
        )


def _flag(value: bool) -> str:
    return "true" if value else "false"


def _event(
    kind: str,
    actor: UserRecord,
    target: UserRecord,
    field: str,
    before: object,
    after: object,
) -> UserAuditRecord:
    return UserAuditRecord(
        event_id=new_user_event_id(),
        event_kind=kind,
        actor_user_id=actor.user_id,
        actor_role=str(actor.role),
        target_user_id=target.user_id,
        field=field,
        value_before=str(before),
        value_after=str(after),
        occurred_at=now(),
    )

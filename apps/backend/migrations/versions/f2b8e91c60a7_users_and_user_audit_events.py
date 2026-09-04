"""users and an append-only user_audit_events trail

Revision ID: f2b8e91c60a7
Revises: d1a7c3e50f42
Create Date: 2026-09-04 11:00:00.000000

Three synthetic staff accounts and the history of changes made to them (ADR-0006).

Two things are deliberate here.

`demo_passcode` is a plain `VARCHAR` and is named for what it is. The login screen prints the
value beside the account it belongs to, so hashing it would protect nothing and would tell the
next person reading this schema that a security boundary exists where none does.

The management trail gets its own table rather than sharing `audit_events`. That table's
`case_id` is `NOT NULL` because every case event has a case; relaxing it to make room for
events that are not about a case would weaken the stronger guarantee to accommodate the weaker
one. Both tables share the same `tilik_audit_append_only()` trigger function, so the two trails
cannot drift apart in what they refuse.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.store.tables import (
    DROP_USER_AUDIT_APPEND_ONLY_TRIGGER_SQL,
    USER_AUDIT_APPEND_ONLY_TRIGGER_SQL,
)

# revision identifiers, used by Alembic.
revision: str = 'f2b8e91c60a7'
down_revision: Union[str, Sequence[str], None] = 'd1a7c3e50f42'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'users',
        sa.Column('user_id', sa.String(length=128), nullable=False),
        sa.Column('staff_token', sa.String(length=32), nullable=False),
        sa.Column('full_name', sa.String(length=160), nullable=False),
        sa.Column('email', sa.String(length=254), nullable=False),
        sa.Column('role', sa.String(length=32), nullable=False),
        sa.Column('demo_passcode', sa.String(length=64), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('last_signed_in_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "role in ('reviewer', 'senior_reviewer', 'admin')", name='ck_users_role'
        ),
        sa.PrimaryKeyConstraint('user_id'),
        sa.UniqueConstraint('staff_token'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('ix_users_role', 'users', ['role'])

    op.create_table(
        'user_audit_events',
        sa.Column('event_id', sa.String(length=128), nullable=False),
        sa.Column('event_kind', sa.String(length=32), nullable=False),
        sa.Column('actor_user_id', sa.String(length=128), nullable=False),
        sa.Column('actor_role', sa.String(length=32), nullable=False),
        sa.Column('target_user_id', sa.String(length=128), nullable=False),
        sa.Column('field', sa.String(length=32), nullable=False),
        sa.Column('value_before', sa.String(length=64), nullable=True),
        sa.Column('value_after', sa.String(length=64), nullable=True),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "event_kind in ('USER_ROLE_CHANGED', 'USER_DEACTIVATED', 'USER_REACTIVATED')",
            name='ck_user_audit_event_kind',
        ),
        sa.PrimaryKeyConstraint('event_id'),
    )
    op.create_index('ix_user_audit_occurred_at', 'user_audit_events', ['occurred_at'])
    op.create_index(
        'ix_user_audit_target', 'user_audit_events', ['target_user_id', 'occurred_at']
    )

    op.execute(USER_AUDIT_APPEND_ONLY_TRIGGER_SQL)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(DROP_USER_AUDIT_APPEND_ONLY_TRIGGER_SQL)
    op.drop_index('ix_user_audit_target', table_name='user_audit_events')
    op.drop_index('ix_user_audit_occurred_at', table_name='user_audit_events')
    op.drop_table('user_audit_events')
    op.drop_index('ix_users_role', table_name='users')
    op.drop_table('users')

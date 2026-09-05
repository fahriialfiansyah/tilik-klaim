"""rename users.staff_token to users.staff_code

Revision ID: a3d5f81b207e
Revises: f2b8e91c60a7
Create Date: 2026-09-05 21:10:00.000000

`token` in this codebase means authentication material: `X-Internal-Token`, and the Bearer JWT
`03_architecture.md` names. `PTG-01` is neither. It is an employee code — it identifies a person,
grants nothing, and is printed on screen beside the account it belongs to.

One word carrying both meanings is a trap with a predictable ending: somebody reads
`staff_token` in a log line or a schema dump and treats it as a credential, either by redacting
something that never needed it or by assuming a boundary that was never here.

A rename, not a new column: the old name has no readers left after this revision, and carrying
both would leave the ambiguity in place under a second name. The unique constraint is renamed
with it so `\\d users` does not still say `token`.
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a3d5f81b207e'
down_revision: Union[str, Sequence[str], None] = 'f2b8e91c60a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Postgres' default name for `UniqueConstraint('staff_token')` on `users`.
OLD_UNIQUE = 'users_staff_token_key'
NEW_UNIQUE = 'users_staff_code_key'


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('users', 'staff_token', new_column_name='staff_code')
    op.execute(f'alter table users rename constraint {OLD_UNIQUE} to {NEW_UNIQUE}')


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(f'alter table users rename constraint {NEW_UNIQUE} to {OLD_UNIQUE}')
    op.alter_column('users', 'staff_code', new_column_name='staff_token')

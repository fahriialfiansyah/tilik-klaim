"""cases: record the billed-line count at screening

Revision ID: d1a7c3e50f42
Revises: c44b0f894fc2
Create Date: 2026-09-01 00:30:00.000000

The queue derived its billed-line count from the number of *unsupported* lines, which made
`supported_lines` zero by construction — a fully supported case reported "0 of 0 lines" and
rendered as having nothing billed at all, contradicting the case detail. The count is a fact
about the screened claim, so it is stored on the case rather than recomputed from the bundle
once per queue row.

Existing rows keep the server default of 0. They are re-screened, or re-seeded, to pick up a
real count; back-filling from the bundle here would mean re-parsing every stored payload inside
a migration, which is the wrong place for it.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd1a7c3e50f42'
down_revision: Union[str, Sequence[str], None] = 'c44b0f894fc2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'cases',
        sa.Column('billed_line_count', sa.Integer(), server_default='0', nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('cases', 'billed_line_count')

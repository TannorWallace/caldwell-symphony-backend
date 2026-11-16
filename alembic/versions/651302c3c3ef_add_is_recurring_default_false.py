"""add is_recurring default false

Revision ID: 651302c3c3ef
Revises: a3eb29ad2730
Create Date: 2026-11-15 15:34:08.144515

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '651302c3c3ef'
down_revision: Union[str, Sequence[str], None] = 'a3eb29ad2730'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'recurring_schedules',
        sa.Column('is_recurring', sa.Boolean(), nullable=False, server_default=sa.false())
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('recurring_schedules', 'is_recurring')
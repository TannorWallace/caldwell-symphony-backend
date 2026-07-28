"""add is_member column to users table

Revision ID: ad8775cd26f7
Revises: 93d528f3ebfe
Create Date: 2026-07-27 11:58:47.694294

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ad8775cd26f7'
down_revision: Union[str, Sequence[str], None] = '93d528f3ebfe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'users',
        sa.Column('is_member', sa.Boolean(), nullable=False, server_default=sa.false())
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'is_member')
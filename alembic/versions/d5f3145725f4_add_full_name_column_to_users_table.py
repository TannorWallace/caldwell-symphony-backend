"""add full_name column to users table

Revision ID: d5f3145725f4
Revises: 17d8603bdf0d
Create Date: 2026-07-15 13:46:18.775365

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd5f3145725f4'
down_revision: Union[str, Sequence[str], None] = '17d8603bdf0d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('full_name', sa.String(length=150), nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'full_name')
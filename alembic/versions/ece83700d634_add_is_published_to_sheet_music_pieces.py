"""add_is_published_to_sheet_music_pieces

Revision ID: ece83700d634
Revises: <your_previous_revision_id>
Create Date: 2026-07-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ece83700d634"
down_revision: Union[str, Sequence[str], None] = "73e5d2f1b1c4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sheet_music_pieces",
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("sheet_music_pieces", "is_published")
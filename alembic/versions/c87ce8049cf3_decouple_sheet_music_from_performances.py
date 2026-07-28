"""decouple_sheet_music_from_performances

Revision ID: c87ce8049cf3
Revises: ece83700d634
Create Date: 2026-07-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c87ce8049cf3"
down_revision: Union[str, Sequence[str], None] = "ece83700d634"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop FK first, then column (name may differ in your DB)
    op.drop_constraint(
        "sheet_music_pieces_performance_id_fkey",
        "sheet_music_pieces",
        type_="foreignkey",
    )
    op.drop_column("sheet_music_pieces", "performance_id")


def downgrade() -> None:
    op.add_column(
        "sheet_music_pieces",
        sa.Column("performance_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "sheet_music_pieces_performance_id_fkey",
        "sheet_music_pieces",
        "performances",
        ["performance_id"],
        ["id"],
    )
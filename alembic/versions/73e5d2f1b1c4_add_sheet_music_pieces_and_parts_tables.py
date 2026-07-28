"""add sheet music pieces and parts tables

Revision ID: 73e5d2f1b1c4
Revises: c3c3805ac393
Create Date: 2026-07-27 13:42:07.068258

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '73e5d2f1b1c4'
down_revision: Union[str, Sequence[str], None] = 'c3c3805ac393'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'sheet_music_pieces',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('performance_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['performance_id'], ['performances.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'sheet_music_parts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('instrument', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=True),
        sa.Column('bucket', sa.String(length=100), nullable=False, server_default='sheet-music'),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('public_url', sa.String(length=500), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('content_type', sa.String(length=100), nullable=True),
        sa.Column('piece_id', sa.Integer(), nullable=False),
        sa.Column('uploaded_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['piece_id'], ['sheet_music_pieces.id']),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('sheet_music_parts')
    op.drop_table('sheet_music_pieces')
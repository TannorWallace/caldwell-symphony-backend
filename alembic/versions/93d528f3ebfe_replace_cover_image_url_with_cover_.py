"""replace cover_image_url with cover_media_id on performances

Revision ID: 93d528f3ebfe
Revises: d5f3145725f4
Create Date: 2026-07-15 15:47:58.381410

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '93d528f3ebfe'
down_revision: Union[str, Sequence[str], None] = 'd5f3145725f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('performances', sa.Column('cover_media_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_performances_cover_media_id_media',
        'performances',
        'media',
        ['cover_media_id'],
        ['id']
    )
    op.drop_column('performances', 'cover_image_url')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('performances', sa.Column('cover_image_url', sa.String(length=500), nullable=True))
    op.drop_constraint('fk_performances_cover_media_id_media', 'performances', type_='foreignkey')
    op.drop_column('performances', 'cover_media_id')
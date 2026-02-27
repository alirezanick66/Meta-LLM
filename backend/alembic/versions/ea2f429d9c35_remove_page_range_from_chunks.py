"""remove_page_range_from_chunks

Revision ID: ea2f429d9c35
Revises: 3d9c51c8711f
Create Date: 2026-02-13 16:43:05.386593

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'ea2f429d9c35'
down_revision: Union[ str, Sequence[ str ], None ] = '3d9c51c8711f'
branch_labels: Union[ str, Sequence[ str ], None ] = None
depends_on: Union[ str, Sequence[ str ], None ] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column( 'chunks', 'page_range' )
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

"""add_composite_indexes_for_performance

Revision ID: f5a8b3c4d6e7
Revises: ea2f429d9c35
Create Date: 2026-02-19 15:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f5a8b3c4d6e7'
down_revision: Union[ str, Sequence[ str ], None ] = 'ea2f429d9c35'
branch_labels: Union[ str, Sequence[ str ], None ] = None
depends_on: Union[ str, Sequence[ str ], None ] = None


def upgrade() -> None:
    """Add composite indexes for better query performance."""
    # Create composite index on (document_id, chunk_index) for ordered retrieval
    op.create_index(
        'idx_document_chunk',
        'chunks',
        ['document_id', 'chunk_index'],
        unique=False
    )

    # Create index on created_at for time-based queries
    op.create_index(
        'idx_created_at',
        'chunks',
        ['created_at'],
        unique=False
    )


def downgrade() -> None:
    """Remove the composite indexes."""
    op.drop_index('idx_document_chunk', table_name='chunks')
    op.drop_index('idx_created_at', table_name='chunks')

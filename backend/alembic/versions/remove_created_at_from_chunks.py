"""remove_created_at_from_chunks

Revision ID: b3f8a2e1d945
Revises: ea2f429d9c35
Create Date: 2026-02-27 

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'b3f8a2e1d945'
down_revision: Union[ str, Sequence[ str ], None ] = 'ea2f429d9c35'
branch_labels: Union[ str, Sequence[ str ], None ] = None
depends_on: Union[ str, Sequence[ str ], None ] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column( 'chunks', 'created_at' )


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        'chunks',
        sa.Column(
            'created_at',
            sa.DateTime( timezone=True ),
            server_default=sa.text( 'now()' ),
            nullable=False,
        ),
    )

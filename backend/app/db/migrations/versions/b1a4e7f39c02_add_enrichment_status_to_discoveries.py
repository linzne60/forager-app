"""add enrichment_status to discoveries

Revision ID: b1a4e7f39c02
Revises: 6fa432ac08cd
Create Date: 2026-04-20 14:30:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b1a4e7f39c02'
down_revision: str | Sequence[str] | None = '6fa432ac08cd'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('discoveries', sa.Column('enrichment_status', sa.String(30), nullable=True, server_default='pending'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('discoveries', 'enrichment_status')

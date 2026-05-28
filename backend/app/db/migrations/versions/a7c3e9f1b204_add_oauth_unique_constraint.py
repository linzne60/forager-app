"""add oauth unique constraint

Revision ID: a7c3e9f1b204
Revises: 238dc6f26cd0
Create Date: 2026-02-21 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a7c3e9f1b204'
down_revision: str | Sequence[str] | None = '238dc6f26cd0'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add unique constraint on (oauth_provider, oauth_id) and drop the old single-column index."""
    op.drop_index(op.f('ix_users_oauth_id'), table_name='users')
    op.create_unique_constraint(
        'uq_users_oauth_provider_oauth_id', 'users', ['oauth_provider', 'oauth_id']
    )


def downgrade() -> None:
    """Remove unique constraint and restore the original single-column index."""
    op.drop_constraint('uq_users_oauth_provider_oauth_id', 'users', type_='unique')
    op.create_index(op.f('ix_users_oauth_id'), 'users', ['oauth_id'], unique=False)

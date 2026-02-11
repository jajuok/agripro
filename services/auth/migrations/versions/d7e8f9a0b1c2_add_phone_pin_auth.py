"""add_phone_pin_auth

Revision ID: d7e8f9a0b1c2
Revises: c6db774423f0
Create Date: 2026-02-09 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd7e8f9a0b1c2'
down_revision: Union[str, Sequence[str], None] = 'c6db774423f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Make email nullable and add auth_method column."""
    # Make email nullable for phone-only users
    op.alter_column('users', 'email', existing_type=sa.String(255), nullable=True)

    # Add auth_method column to distinguish email vs phone_pin accounts
    op.add_column('users', sa.Column('auth_method', sa.String(20),
                  server_default='email', nullable=False))


def downgrade() -> None:
    """Revert: remove auth_method and make email required again."""
    op.drop_column('users', 'auth_method')
    op.alter_column('users', 'email', existing_type=sa.String(255), nullable=False)

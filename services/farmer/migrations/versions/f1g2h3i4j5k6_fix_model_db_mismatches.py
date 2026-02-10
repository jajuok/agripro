"""fix model-db column mismatches

Revision ID: f1g2h3i4j5k6
Revises: e0f5g6h7i8j9
Create Date: 2026-02-09 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f1g2h3i4j5k6'
down_revision: Union[str, Sequence[str], None] = 'e0f5g6h7i8j9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add missing columns to align models with database."""
    # farm_documents: add missing columns
    op.add_column('farm_documents',
        sa.Column('document_number', sa.String(length=100), nullable=True))
    op.add_column('farm_documents',
        sa.Column('verification_status', sa.String(length=50),
                   nullable=False, server_default='pending'))

    # crop_records: add missing columns
    op.add_column('crop_records',
        sa.Column('year', sa.Integer(), nullable=True))
    op.add_column('crop_records',
        sa.Column('is_current', sa.Boolean(),
                   nullable=False, server_default='false'))
    op.add_column('crop_records',
        sa.Column('notes', sa.Text(), nullable=True))

    # soil_test_reports: add missing column
    op.add_column('soil_test_reports',
        sa.Column('tested_by', sa.String(length=200), nullable=True))


def downgrade() -> None:
    """Remove added columns."""
    op.drop_column('soil_test_reports', 'tested_by')
    op.drop_column('crop_records', 'notes')
    op.drop_column('crop_records', 'is_current')
    op.drop_column('crop_records', 'year')
    op.drop_column('farm_documents', 'verification_status')
    op.drop_column('farm_documents', 'document_number')

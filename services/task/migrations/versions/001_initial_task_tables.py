"""Initial task tables

Revision ID: 001
Revises:
Create Date: 2026-02-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('farmer_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('farm_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(50), nullable=False, server_default='general'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True, index=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('assigned_to', sa.String(200), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('recurrence', sa.String(20), nullable=False, server_default='none'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'task_comments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('task_comments')
    op.drop_table('tasks')

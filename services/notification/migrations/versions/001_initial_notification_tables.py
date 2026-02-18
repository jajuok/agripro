"""initial notification tables

Revision ID: 001
Revises:
Create Date: 2026-02-18
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Notification templates
    op.create_table(
        "notification_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(100), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("notification_type", sa.String(20), nullable=False, server_default="info"),
        sa.Column("priority", sa.String(20), nullable=False, server_default="normal"),
        sa.Column("title_template", sa.String(255), nullable=False),
        sa.Column("body_template", sa.Text, nullable=False),
        sa.Column("sms_template", sa.String(160), nullable=True),
        sa.Column("channels", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Notifications
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("notification_type", sa.String(20), nullable=False, server_default="info"),
        sa.Column("priority", sa.String(20), nullable=False, server_default="normal"),
        sa.Column("data", postgresql.JSONB, nullable=True),
        sa.Column(
            "template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("notification_templates.id"),
            nullable=True,
        ),
        sa.Column("is_read", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index(
        "ix_notifications_user_created", "notifications", ["user_id", "created_at"]
    )
    op.create_index(
        "ix_notifications_user_unread", "notifications", ["user_id", "is_read"]
    )

    # Notification preferences
    op.create_table(
        "notification_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True
        ),
        sa.Column("push_enabled", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("sms_enabled", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("email_enabled", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("scheme_deadlines", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("weather_alerts", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("task_reminders", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("crop_alerts", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("market_prices", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("push_subscription", postgresql.JSONB, nullable=True),
        sa.Column("sms_phone_number", sa.String(20), nullable=True),
        sa.Column("quiet_hours_start", sa.Time, nullable=True),
        sa.Column("quiet_hours_end", sa.Time, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_notification_preferences_user_id",
        "notification_preferences",
        ["user_id"],
        unique=True,
    )

    # Delivery logs
    op.create_table(
        "delivery_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "notification_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("notifications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("provider_message_id", sa.String(255), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("cost", sa.Float, nullable=True),
        sa.Column("currency", sa.String(10), nullable=True),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_delivery_logs_notification_id", "delivery_logs", ["notification_id"]
    )


def downgrade() -> None:
    op.drop_table("delivery_logs")
    op.drop_table("notification_preferences")
    op.drop_table("notifications")
    op.drop_table("notification_templates")

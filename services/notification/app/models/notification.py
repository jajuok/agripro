"""Notification database models."""

import uuid
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    Time,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship

from app.core.db_types import JSONBCompatible


class Base(DeclarativeBase):
    pass


class NotificationType(str, PyEnum):
    INFO = "info"
    WARNING = "warning"
    URGENT = "urgent"
    SUCCESS = "success"


class NotificationPriority(str, PyEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class DeliveryChannel(str, PyEnum):
    IN_APP = "in_app"
    SMS = "sms"
    PUSH = "push"
    EMAIL = "email"


class DeliveryStatus(str, PyEnum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    SKIPPED = "skipped"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    notification_type = Column(String(20), nullable=False, default=NotificationType.INFO.value)
    priority = Column(String(20), nullable=False, default=NotificationPriority.NORMAL.value)
    data = Column(JSONBCompatible, nullable=True)
    template_id = Column(UUID(as_uuid=True), ForeignKey("notification_templates.id"), nullable=True)
    is_read = Column(Boolean, nullable=False, default=False)
    read_at = Column(DateTime(timezone=True), nullable=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    template = relationship("NotificationTemplate", back_populates="notifications")
    delivery_logs = relationship(
        "DeliveryLog", back_populates="notification", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_notifications_user_created", "user_id", "created_at"),
        Index("ix_notifications_user_unread", "user_id", "is_read"),
    )


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)

    # Channel toggles
    push_enabled = Column(Boolean, nullable=False, default=True)
    sms_enabled = Column(Boolean, nullable=False, default=True)
    email_enabled = Column(Boolean, nullable=False, default=False)

    # Category toggles
    scheme_deadlines = Column(Boolean, nullable=False, default=True)
    weather_alerts = Column(Boolean, nullable=False, default=True)
    task_reminders = Column(Boolean, nullable=False, default=True)
    crop_alerts = Column(Boolean, nullable=False, default=True)
    market_prices = Column(Boolean, nullable=False, default=True)

    # Push subscription (VAPID)
    push_subscription = Column(JSONBCompatible, nullable=True)

    # SMS
    sms_phone_number = Column(String(20), nullable=True)

    # Quiet hours
    quiet_hours_start = Column(Time, nullable=True)
    quiet_hours_end = Column(Time, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class NotificationTemplate(Base):
    __tablename__ = "notification_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(100), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    notification_type = Column(String(20), nullable=False, default=NotificationType.INFO.value)
    priority = Column(String(20), nullable=False, default=NotificationPriority.NORMAL.value)
    title_template = Column(String(255), nullable=False)
    body_template = Column(Text, nullable=False)
    sms_template = Column(String(160), nullable=True)
    channels = Column(JSONBCompatible, nullable=False, default=list)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    notifications = relationship("Notification", back_populates="template")


class DeliveryLog(Base):
    __tablename__ = "delivery_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    notification_id = Column(
        UUID(as_uuid=True),
        ForeignKey("notifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    channel = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default=DeliveryStatus.PENDING.value)
    provider_message_id = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)
    cost = Column(Float, nullable=True)
    currency = Column(String(10), nullable=True)
    attempted_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)

    notification = relationship("Notification", back_populates="delivery_logs")

"""Pydantic schemas for notification service."""

from datetime import datetime, time
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

# --- Notification ---


class NotificationCreate(BaseModel):
    user_id: UUID
    title: str = ""
    body: str = ""
    notification_type: str = "info"
    priority: str = "normal"
    data: dict[str, Any] | None = None
    template_code: str | None = None
    template_variables: dict[str, str] | None = None
    channels: list[str] | None = None


class NotificationBulkCreate(BaseModel):
    user_ids: list[UUID]
    title: str = ""
    body: str = ""
    notification_type: str = "info"
    priority: str = "normal"
    data: dict[str, Any] | None = None
    template_code: str | None = None
    template_variables: dict[str, str] | None = None
    channels: list[str] | None = None


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    title: str
    body: str
    notification_type: str
    priority: str
    data: dict[str, Any] | None = None
    is_read: bool
    read_at: datetime | None = None
    scheduled_at: datetime | None = None
    expires_at: datetime | None = None
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    unread_count: int
    page: int
    page_size: int


# --- Preferences ---


class PreferenceUpdate(BaseModel):
    push_enabled: bool | None = None
    sms_enabled: bool | None = None
    email_enabled: bool | None = None
    scheme_deadlines: bool | None = None
    weather_alerts: bool | None = None
    task_reminders: bool | None = None
    crop_alerts: bool | None = None
    market_prices: bool | None = None
    sms_phone_number: str | None = None
    quiet_hours_start: time | None = None
    quiet_hours_end: time | None = None


class PreferenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    push_enabled: bool
    sms_enabled: bool
    email_enabled: bool
    scheme_deadlines: bool
    weather_alerts: bool
    task_reminders: bool
    crop_alerts: bool
    market_prices: bool
    push_subscription: dict[str, Any] | None = None
    sms_phone_number: str | None = None
    quiet_hours_start: time | None = None
    quiet_hours_end: time | None = None
    created_at: datetime
    updated_at: datetime


class PushSubscription(BaseModel):
    endpoint: str
    keys: dict[str, str]


# --- Templates ---


class TemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    notification_type: str
    priority: str
    title_template: str
    body_template: str
    sms_template: str | None = None
    channels: list[str]
    is_active: bool
    created_at: datetime


# --- Delivery Logs ---


class DeliveryLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    notification_id: UUID
    channel: str
    status: str
    provider_message_id: str | None = None
    error_message: str | None = None
    cost: float | None = None
    currency: str | None = None
    attempted_at: datetime | None = None
    delivered_at: datetime | None = None


class UnreadCountResponse(BaseModel):
    unread_count: int

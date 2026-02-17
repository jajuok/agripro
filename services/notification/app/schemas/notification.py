"""Pydantic schemas for notification service."""

from datetime import datetime, time
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# --- Notification ---


class NotificationCreate(BaseModel):
    user_id: UUID
    title: str = ""
    body: str = ""
    notification_type: str = "info"
    priority: str = "normal"
    data: Optional[dict[str, Any]] = None
    template_code: Optional[str] = None
    template_variables: Optional[dict[str, str]] = None
    channels: Optional[list[str]] = None


class NotificationBulkCreate(BaseModel):
    user_ids: list[UUID]
    title: str = ""
    body: str = ""
    notification_type: str = "info"
    priority: str = "normal"
    data: Optional[dict[str, Any]] = None
    template_code: Optional[str] = None
    template_variables: Optional[dict[str, str]] = None
    channels: Optional[list[str]] = None


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    title: str
    body: str
    notification_type: str
    priority: str
    data: Optional[dict[str, Any]] = None
    is_read: bool
    read_at: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    unread_count: int
    page: int
    page_size: int


# --- Preferences ---


class PreferenceUpdate(BaseModel):
    push_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    email_enabled: Optional[bool] = None
    scheme_deadlines: Optional[bool] = None
    weather_alerts: Optional[bool] = None
    task_reminders: Optional[bool] = None
    crop_alerts: Optional[bool] = None
    market_prices: Optional[bool] = None
    sms_phone_number: Optional[str] = None
    quiet_hours_start: Optional[time] = None
    quiet_hours_end: Optional[time] = None


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
    push_subscription: Optional[dict[str, Any]] = None
    sms_phone_number: Optional[str] = None
    quiet_hours_start: Optional[time] = None
    quiet_hours_end: Optional[time] = None
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
    sms_template: Optional[str] = None
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
    provider_message_id: Optional[str] = None
    error_message: Optional[str] = None
    cost: Optional[float] = None
    currency: Optional[str] = None
    attempted_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None


class UnreadCountResponse(BaseModel):
    unread_count: int

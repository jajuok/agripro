"""Core notification service."""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import (
    DeliveryChannel,
    DeliveryLog,
    DeliveryStatus,
    Notification,
    NotificationPreference,
    NotificationTemplate,
)

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # --- Notifications ---

    async def create_notification(
        self,
        user_id: UUID,
        title: str,
        body: str,
        notification_type: str = "info",
        priority: str = "normal",
        data: dict | None = None,
        template_code: str | None = None,
        template_variables: dict | None = None,
        channels: list[str] | None = None,
    ) -> Notification:
        template = None
        if template_code:
            result = await self.db.execute(
                select(NotificationTemplate).where(
                    NotificationTemplate.code == template_code,
                    NotificationTemplate.is_active.is_(True),
                )
            )
            template = result.scalar_one_or_none()
            if template:
                variables = template_variables or {}
                title = template.title_template.format(**variables)
                body = template.body_template.format(**variables)
                notification_type = template.notification_type
                priority = template.priority
                if not channels:
                    channels = template.channels or []

        notification = Notification(
            user_id=user_id,
            title=title,
            body=body,
            notification_type=notification_type,
            priority=priority,
            data=data,
            template_id=template.id if template else None,
        )
        self.db.add(notification)
        await self.db.flush()

        # Determine delivery channels
        if not channels:
            channels = [DeliveryChannel.IN_APP.value]

        prefs = await self.get_preferences(user_id)

        for channel in channels:
            should_deliver = True
            if (
                channel == DeliveryChannel.SMS.value
                and prefs
                and not prefs.sms_enabled
                or channel == DeliveryChannel.PUSH.value
                and prefs
                and not prefs.push_enabled
                or channel == DeliveryChannel.EMAIL.value
                and prefs
                and not prefs.email_enabled
            ):
                should_deliver = False

            log = DeliveryLog(
                notification_id=notification.id,
                channel=channel,
                status=DeliveryStatus.PENDING.value
                if should_deliver
                else DeliveryStatus.SKIPPED.value,
            )
            self.db.add(log)

        await self.db.flush()
        return notification

    async def list_notifications(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        unread_only: bool = False,
    ) -> tuple[list[Notification], int, int]:
        query = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            query = query.where(Notification.is_read.is_(False))
        query = query.order_by(Notification.created_at.desc())

        # Total count
        count_q = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_q)).scalar() or 0

        # Unread count
        unread_q = select(func.count()).where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
        unread_count = (await self.db.execute(unread_q)).scalar() or 0

        # Paginated results
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total, unread_count

    async def mark_as_read(self, notification_id: UUID, user_id: UUID) -> Notification | None:
        result = await self.db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )
        notification = result.scalar_one_or_none()
        if notification and not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.now(UTC)
            await self.db.flush()
        return notification

    async def mark_all_as_read(self, user_id: UUID) -> int:
        result = await self.db.execute(
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
            .values(is_read=True, read_at=datetime.now(UTC))
        )
        await self.db.flush()
        return result.rowcount

    async def get_unread_count(self, user_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count()).where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
        )
        return result.scalar() or 0

    # --- Preferences ---

    async def get_preferences(self, user_id: UUID) -> NotificationPreference | None:
        result = await self.db.execute(
            select(NotificationPreference).where(NotificationPreference.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def upsert_preferences(self, user_id: UUID, updates: dict) -> NotificationPreference:
        pref = await self.get_preferences(user_id)
        if pref is None:
            pref = NotificationPreference(user_id=user_id)
            self.db.add(pref)

        for key, value in updates.items():
            if value is not None and hasattr(pref, key):
                setattr(pref, key, value)

        await self.db.flush()
        return pref

    async def save_push_subscription(
        self, user_id: UUID, subscription: dict
    ) -> NotificationPreference:
        pref = await self.get_preferences(user_id)
        if pref is None:
            pref = NotificationPreference(user_id=user_id)
            self.db.add(pref)

        pref.push_subscription = subscription
        pref.push_enabled = True
        await self.db.flush()
        return pref

    # --- Delivery ---

    async def get_pending_deliveries(self, limit: int = 50) -> list[DeliveryLog]:
        result = await self.db.execute(
            select(DeliveryLog)
            .where(DeliveryLog.status == DeliveryStatus.PENDING.value)
            .order_by(DeliveryLog.id)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_delivery_status(
        self,
        delivery_id: UUID,
        status: str,
        provider_message_id: str | None = None,
        error_message: str | None = None,
        cost: float | None = None,
        currency: str | None = None,
    ) -> DeliveryLog | None:
        result = await self.db.execute(select(DeliveryLog).where(DeliveryLog.id == delivery_id))
        log = result.scalar_one_or_none()
        if log:
            log.status = status
            log.attempted_at = datetime.now(UTC)
            if status == DeliveryStatus.DELIVERED.value:
                log.delivered_at = datetime.now(UTC)
            if provider_message_id:
                log.provider_message_id = provider_message_id
            if error_message:
                log.error_message = error_message
            if cost is not None:
                log.cost = cost
            if currency:
                log.currency = currency
            await self.db.flush()
        return log

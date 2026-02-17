"""Seed default notification templates."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import NotificationTemplate

logger = logging.getLogger(__name__)

DEFAULT_TEMPLATES = [
    {
        "code": "scheme_deadline_7d",
        "name": "Scheme Deadline - 7 Days",
        "notification_type": "warning",
        "priority": "high",
        "title_template": "Scheme deadline in 7 days: {scheme_name}",
        "body_template": "The application deadline for {scheme_name} is in 7 days ({deadline_date}). Don't miss out!",
        "sms_template": "Reminder: {scheme_name} deadline in 7 days ({deadline_date}). Apply now!",
        "channels": ["in_app", "sms", "push"],
    },
    {
        "code": "scheme_deadline_1d",
        "name": "Scheme Deadline - 1 Day",
        "notification_type": "urgent",
        "priority": "critical",
        "title_template": "URGENT: {scheme_name} deadline tomorrow!",
        "body_template": "Tomorrow is the last day to apply for {scheme_name}. Submit your application before {deadline_date}.",
        "sms_template": "URGENT: {scheme_name} deadline TOMORROW {deadline_date}. Apply now!",
        "channels": ["in_app", "sms", "push"],
    },
    {
        "code": "application_approved",
        "name": "Application Approved",
        "notification_type": "success",
        "priority": "high",
        "title_template": "Application Approved: {scheme_name}",
        "body_template": "Congratulations! Your application for {scheme_name} has been approved. {details}",
        "sms_template": "Your {scheme_name} application has been APPROVED! Check the app for details.",
        "channels": ["in_app", "sms"],
    },
    {
        "code": "application_rejected",
        "name": "Application Rejected",
        "notification_type": "warning",
        "priority": "high",
        "title_template": "Application Update: {scheme_name}",
        "body_template": "Your application for {scheme_name} was not approved. Reason: {reason}. You may re-apply if eligible.",
        "sms_template": "Your {scheme_name} application was not approved. Check the app for details.",
        "channels": ["in_app", "sms"],
    },
    {
        "code": "weather_alert",
        "name": "Weather Alert",
        "notification_type": "urgent",
        "priority": "critical",
        "title_template": "Weather Alert: {alert_type}",
        "body_template": "{alert_type} expected in {location}. {description}. Take necessary precautions for your crops.",
        "sms_template": "WEATHER ALERT: {alert_type} in {location}. {description}",
        "channels": ["in_app", "sms", "push"],
    },
    {
        "code": "task_reminder",
        "name": "Task Reminder",
        "notification_type": "info",
        "priority": "normal",
        "title_template": "Task Due: {task_name}",
        "body_template": "Your task '{task_name}' is due {due_info}. Tap to view details.",
        "sms_template": None,
        "channels": ["in_app", "push"],
    },
    {
        "code": "crop_alert",
        "name": "Crop Alert",
        "notification_type": "warning",
        "priority": "high",
        "title_template": "Crop Alert: {crop_name}",
        "body_template": "{alert_message} for your {crop_name} crop. {recommendation}",
        "sms_template": None,
        "channels": ["in_app", "push"],
    },
]


async def seed_templates(db: AsyncSession) -> None:
    """Seed default templates idempotently."""
    for tmpl_data in DEFAULT_TEMPLATES:
        result = await db.execute(
            select(NotificationTemplate).where(NotificationTemplate.code == tmpl_data["code"])
        )
        existing = result.scalar_one_or_none()
        if existing is None:
            template = NotificationTemplate(**tmpl_data)
            db.add(template)
            logger.info("Seeded template: %s", tmpl_data["code"])

    await db.commit()
    logger.info("Template seeding complete")

"""VAPID Web Push service."""

import json
import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


class WebPushService:
    def __init__(self):
        self._configured = bool(settings.vapid_private_key and settings.vapid_public_key)
        if self._configured:
            logger.info("Web Push (VAPID) configured")
        else:
            logger.debug("Web Push (VAPID) not configured, push will be skipped")

    async def send_push(
        self,
        subscription_info: dict,
        title: str,
        body: str,
        data: dict[str, Any] | None = None,
    ) -> bool:
        if not self._configured:
            logger.debug("Web Push not configured, skipping")
            return False

        try:
            from pywebpush import webpush

            payload = json.dumps({"title": title, "body": body, "data": data or {}})

            webpush(
                subscription_info=subscription_info,
                data=payload,
                vapid_private_key=settings.vapid_private_key,
                vapid_claims={"sub": f"mailto:{settings.vapid_claims_email}"},
            )
            logger.info("Web Push sent successfully")
            return True
        except Exception as e:
            logger.error("Web Push failed: %s", e)
            return False

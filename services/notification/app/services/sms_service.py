"""Africa's Talking SMS service."""

import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class SMSService:
    def __init__(self):
        self._client = None
        self._sms = None
        if settings.at_username and settings.at_api_key:
            try:
                import africastalking

                africastalking.initialize(settings.at_username, settings.at_api_key)
                self._sms = africastalking.SMS
                logger.info("Africa's Talking SMS initialized")
            except Exception as e:
                logger.warning("Failed to initialize Africa's Talking: %s", e)

    async def send_sms(self, phone: str, message: str) -> dict | None:
        if not self._sms:
            logger.debug("SMS not configured, skipping send to %s", phone)
            return None

        try:
            response = self._sms.send(
                message,
                [phone],
                sender_id=settings.at_sender_id or None,
            )
            logger.info("SMS sent to %s: %s", phone, response)
            return response
        except Exception as e:
            logger.error("SMS send failed to %s: %s", phone, e)
            return {"error": str(e)}

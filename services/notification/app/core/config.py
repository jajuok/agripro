"""Application configuration."""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    app_name: str = "notification-service"
    debug: bool = False
    environment: str = "development"

    host: str = "0.0.0.0"
    port: int = 9011

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/agrischeme_notification"
    redis_url: str = "redis://localhost:6379/10"

    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8081"]

    # Africa's Talking SMS
    at_username: str = ""
    at_api_key: str = ""
    at_sender_id: str = ""

    # VAPID Web Push
    vapid_private_key: str = ""
    vapid_public_key: str = ""
    vapid_claims_email: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

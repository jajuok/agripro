"""Application configuration."""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    app_name: str = "farmer-service"
    debug: bool = False
    environment: str = "development"

    host: str = "0.0.0.0"
    port: int = 8001

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/agrischeme_farmer"
    redis_url: str = "redis://localhost:6379/1"

    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8081"]

    # Auth service
    auth_service_url: str = "http://localhost:8000"

    # S3/Storage
    s3_bucket: str = "agrischeme-documents"
    s3_region: str = "us-east-1"

    # Biometric service
    biometric_service_url: str = ""

    # Identity verification
    identity_service_url: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

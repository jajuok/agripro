"""Application configuration."""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    app_name: str = "task-service"
    debug: bool = False
    environment: str = "development"

    host: str = "0.0.0.0"
    port: int = 8000

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/agrischeme_task"
    redis_url: str = "redis://localhost:6379/8"

    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8081"]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

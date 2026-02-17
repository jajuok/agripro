"""Application configuration."""

from functools import lru_cache

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

    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8081"]

    # Auth service
    auth_service_url: str = "http://localhost:8000"

    # S3/Storage
    s3_bucket: str = "agrischeme-documents"
    s3_region: str = "us-east-1"
    s3_endpoint_url: str | None = None  # For MinIO or local S3-compatible storage
    s3_access_key: str = ""
    s3_secret_key: str = ""

    # Biometric service
    biometric_service_url: str = ""

    # Identity verification (IPRS, NIN, etc.)
    iprs_api_url: str = ""
    iprs_api_key: str = ""

    # Credit Bureau
    credit_bureau_url: str = ""
    credit_bureau_api_key: str = ""

    # Sanctions Screening
    worldcheck_url: str = ""
    worldcheck_api_key: str = ""

    # OCR Service
    ocr_provider: str = "tesseract"  # tesseract, aws_textract, google_vision, azure_form


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

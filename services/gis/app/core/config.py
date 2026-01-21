"""GIS Service configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_prefix="GIS_",
        env_file=".env",
    )

    # Project
    PROJECT_NAME: str = "GIS Service"
    API_V1_STR: str = "/api/v1"

    # Service info
    service_name: str = "gis-service"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 9003

    # CORS
    cors_origins: list[str] = ["*"]

    # Kenya boundary data (could be a file path or URL)
    kenya_boundary_data_path: str = "data/kenya_boundaries.geojson"


settings = Settings()

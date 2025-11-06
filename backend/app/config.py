"""
Application Configuration

Uses pydantic-settings for type-safe configuration from environment variables.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "Minifigure-Stonks API"
    app_version: str = "0.1.0"
    debug: bool = True
    api_version: str = "v1"

    # Database
    database_url: str = "postgresql://minifig_user:minifig_dev_password@localhost:5432/minifigure_stonks"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # BrickLink API (optional for now)
    bricklink_consumer_key: str = ""
    bricklink_consumer_secret: str = ""
    bricklink_token_value: str = ""
    bricklink_token_secret: str = ""

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Using @lru_cache ensures we only create one Settings instance,
    which is reused across the application.

    Returns:
        Settings instance with environment variables loaded
    """
    return Settings()

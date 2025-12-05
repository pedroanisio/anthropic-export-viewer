"""
Application configuration using pydantic-settings (ADR-011, ADR-071).

Environment variables can be set directly or via .env file.
"""

from __future__ import annotations

import secrets
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Flask Configuration
    secret_key: str = Field(
        default_factory=lambda: secrets.token_hex(32),
        description="Flask secret key for session management",
    )
    flask_env: Literal["development", "production", "testing"] = Field(
        default="development",
        description="Flask environment mode",
    )
    debug: bool = Field(
        default=False,
        description="Enable Flask debug mode",
    )

    # Server Configuration
    host: str = Field(
        default="0.0.0.0",
        description="Server host address",
    )
    port: int = Field(
        default=5000,
        ge=1,
        le=65535,
        description="Server port number",
    )

    # MongoDB Configuration
    mongo_uri: str = Field(
        default="mongodb://localhost:27017/",
        description="MongoDB connection URI",
    )
    db_name: str = Field(
        default="anthropic_data",
        description="MongoDB database name",
    )

    # Upload Configuration
    upload_folder: str = Field(
        default="./uploads",
        description="Directory for file uploads",
    )
    max_content_length: int = Field(
        default=500 * 1024 * 1024,  # 500MB
        ge=1024,
        description="Maximum upload file size in bytes",
    )

    # Logging Configuration
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Application log level",
    )
    log_format: Literal["json", "console"] = Field(
        default="console",
        description="Log output format",
    )

    @field_validator("flask_env", mode="before")
    @classmethod
    def validate_flask_env(cls, v: str) -> str:
        """Normalize flask environment value."""
        if isinstance(v, str):
            return v.lower()
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.flask_env == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.flask_env == "development"

    @property
    def is_testing(self) -> bool:
        """Check if running in testing mode."""
        return self.flask_env == "testing"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.

    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()


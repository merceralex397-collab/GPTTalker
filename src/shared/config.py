"""Shared configuration patterns."""

import logging
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class SharedConfig(BaseSettings):
    """Base configuration that both hub and node agent can inherit from."""

    # Logging settings
    log_level: str = Field("INFO", description="Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    log_format: Literal["json", "text"] = Field("json", description="Log format type")

    # Trace settings
    trace_id_header: str = Field("X-Trace-ID", description="HTTP header name for trace ID")

    # Database settings
    database_path: str = Field("data/gpttalker.db", description="Path to SQLite database file")

    model_config = SettingsConfigDict(
        env_prefix="GPTTALKER_",
        extra="allow",
        case_sensitive=False,
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the allowed values."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        level = v.upper()
        if level not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}, got {v}")
        return level


def get_shared_config() -> SharedConfig:
    """Get shared configuration.

    Returns:
        SharedConfig instance with environment overrides.
    """
    return SharedConfig()


def configure_logging_from_config(config: SharedConfig) -> None:
    """Configure logging based on shared config.

    Args:
        config: SharedConfig instance with logging settings.
    """
    import sys

    log_level = getattr(logging, config.log_level.upper())

    # Set up basic logging with the configured level
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )

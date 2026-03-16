"""Hub configuration loading."""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class HubConfig(BaseSettings):
    """Configuration for the GPTTalker hub."""

    # Server settings
    host: str = Field("0.0.0.0", description="Server host to bind to")
    port: int = Field(8000, ge=1, le=65535, description="Server port")

    # CORS settings
    cors_origins: list[str] | str | None = Field(
        None,
        description="CORS allowed origins (comma-separated or JSON array, '*' for all)",
    )

    # Logging settings
    log_level: str = Field("INFO", description="Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    log_format: str = Field("json", description="Log format type (json or text)")

    # Database settings
    database_url: str = Field(
        "sqlite+aiosqlite:///gpttalker.db", description="Database connection URL"
    )

    # Qdrant settings
    qdrant_host: str = Field("localhost", description="Qdrant server host")
    qdrant_port: int = Field(6333, ge=1, le=65535, description="Qdrant server port")

    # Node agent settings
    node_agent_timeout: int = Field(30, ge=1, description="Node agent request timeout in seconds")

    # Node client settings (for hub-to-node communication)
    node_client_timeout: float = Field(
        30.0, ge=1.0, description="Default node request timeout in seconds"
    )
    node_client_connect_timeout: float = Field(
        5.0, ge=0.1, description="Node connect timeout in seconds"
    )
    node_client_pool_max_connections: int = Field(
        10, ge=1, description="Max connections per node pool"
    )
    node_client_pool_max_keepalive: int = Field(20, ge=1, description="Max keepalive connections")
    node_client_api_key: str | None = Field(None, description="API key for node authentication")

    model_config = SettingsConfigDict(
        env_prefix="GPTTALKER_",
        extra="allow",
        case_sensitive=False,
    )

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format."""
        if not v:
            raise ValueError("database_url cannot be empty")
        # Allow sqlite, sqlite+aiosqlite, postgresql, etc.
        valid_prefixes = ("sqlite", "postgresql", "mysql")
        if not any(v.startswith(prefix) for prefix in valid_prefixes):
            raise ValueError(f"database_url must start with one of {valid_prefixes}")
        return v

    @field_validator("host")
    @classmethod
    def validate_host(cls, v: str) -> str:
        """Validate host is not empty."""
        if not v or not v.strip():
            raise ValueError("host cannot be empty")
        return v.strip()

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the allowed values."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        level = v.upper()
        if level not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}, got {v}")
        return level

    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        """Validate log format is one of the allowed values."""
        valid_formats = {"json", "text"}
        format_lower = v.lower()
        if format_lower not in valid_formats:
            raise ValueError(f"log_format must be one of {valid_formats}, got {v}")
        return format_lower


def get_hub_config() -> HubConfig:
    """Get hub configuration from environment.

    Returns:
        HubConfig instance with environment overrides.
    """
    return HubConfig()

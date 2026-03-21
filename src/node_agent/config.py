"""Node agent configuration."""

import os

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class NodeAgentConfig(BaseSettings):
    """Configuration for the node agent."""

    # Identity settings
    node_name: str = Field("node-agent", description="Node agent name/identifier")
    hub_url: str = Field("http://localhost:8000", description="Hub URL to connect to")

    # Authentication
    api_key: str | None = Field(None, description="API key for hub authentication")

    # Operation settings
    operation_timeout: int = Field(60, ge=1, description="Operation timeout in seconds")
    max_file_size: int = Field(
        10 * 1024 * 1024,  # 10MB
        ge=0,
        description="Maximum file size in bytes",
    )

    # Allowed paths (for security)
    allowed_repos: list[str] = Field(
        default_factory=list, description="List of allowed repository paths"
    )
    allowed_write_targets: list[str] = Field(
        default_factory=list, description="List of allowed write target paths"
    )

    model_config = SettingsConfigDict(
        env_prefix="GPTTALKER_NODE_",
        extra="ignore",
        case_sensitive=False,
    )

    @field_validator("node_name")
    @classmethod
    def validate_node_name(cls, v: str) -> str:
        """Validate node name is not empty and matches pattern."""
        if not v or not v.strip():
            raise ValueError("node_name cannot be empty")
        import re

        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("node_name must match pattern ^[a-zA-Z0-9_-]+$")
        return v.strip()

    @field_validator("hub_url")
    @classmethod
    def validate_hub_url(cls, v: str) -> str:
        """Validate hub URL is a valid URL."""
        if not v or not v.strip():
            raise ValueError("hub_url cannot be empty")
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("hub_url must start with http:// or https://")
        return v.strip()

    @field_validator("allowed_repos", "allowed_write_targets")
    @classmethod
    def validate_paths(cls, v: list[str]) -> list[str]:
        """Validate that paths are absolute if provided."""
        for path in v:
            if path and not os.path.isabs(path):
                raise ValueError(f"Path '{path}' must be absolute")
        return v


def get_node_agent_config() -> NodeAgentConfig:
    """Get node agent configuration from environment.

    Returns:
        NodeAgentConfig instance with environment overrides.
    """
    return NodeAgentConfig()

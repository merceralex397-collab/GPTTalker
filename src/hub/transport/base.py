"""Base transport protocol classes for MCP communication."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TransportError(Exception):
    """Base exception for transport-level errors."""

    pass


class TransportStatus(Enum):
    """Status codes for transport operations."""

    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    UNAUTHORIZED = "unauthorized"
    NOT_FOUND = "not_found"


@dataclass
class TransportResult:
    """Standardized transport result wrapper.

    This class wraps the result of any transport operation with
    standardized metadata including status, duration, and error info.
    """

    status: TransportStatus
    data: Any = None
    error: str | None = None
    duration_ms: int = 0

    @property
    def is_success(self) -> bool:
        """Check if the transport operation was successful."""
        return self.status == TransportStatus.SUCCESS

    @property
    def is_error(self) -> bool:
        """Check if the transport operation failed."""
        return self.status in (
            TransportStatus.ERROR,
            TransportStatus.TIMEOUT,
            TransportStatus.UNAUTHORIZED,
            TransportStatus.NOT_FOUND,
        )


class TransportProtocol(ABC):
    """Abstract base class for transport implementations.

    This defines the interface that all transport implementations
    (HTTP, WebSocket, etc.) must follow.
    """

    @abstractmethod
    async def send(self, message: dict[str, Any]) -> TransportResult:
        """Send a message through the transport.

        Args:
            message: The message to send.

        Returns:
            TransportResult with the response and metadata.
        """
        pass

    @abstractmethod
    async def receive(self) -> dict[str, Any] | None:
        """Receive a message from the transport.

        Returns:
            The received message, or None if no message is available.
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the transport connection."""
        pass


@dataclass
class MCPMessage:
    """MCP message model for request/response handling.

    Represents a single MCP protocol message with metadata
    for tracing and correlation.
    """

    message_type: str  # "request" | "response" | "notification"
    method: str | None = None  # e.g., "tools/call", "tools/list"
    params: dict[str, Any] = field(default_factory=dict)
    id: str | None = None  # Correlation ID
    trace_id: str | None = None
    result: Any = None
    error: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary representation.

        Returns:
            Dictionary representation of the message.
        """
        result: dict[str, Any] = {
            "jsonrpc": "2.0",
            "type": self.message_type,
        }

        if self.method:
            result["method"] = self.method
        if self.params:
            result["params"] = self.params
        if self.id is not None:
            result["id"] = self.id
        if self.result is not None:
            result["result"] = self.result
        if self.error:
            result["error"] = self.error

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MCPMessage":
        """Create message from dictionary representation.

        Args:
            data: Dictionary containing message data.

        Returns:
            MCPMessage instance.
        """
        return cls(
            message_type=data.get("type", "request"),
            method=data.get("method"),
            params=data.get("params", {}),
            id=data.get("id"),
            result=data.get("result"),
            error=data.get("error"),
        )

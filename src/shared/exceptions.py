"""Shared exception classes for GPTTalker."""

from typing import Any


class GPTTalkerError(Exception):
    """Base exception for GPTTalker.

    Supports trace_id for request tracking in error responses.
    """

    def __init__(
        self,
        message: str,
        trace_id: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        """Initialize GPTTalker error.

        Args:
            message: Error message.
            trace_id: Optional trace ID for tracking.
            details: Optional additional error details.
        """
        super().__init__(message)
        self.message = message
        self.trace_id = trace_id
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for API responses.

        Returns:
            Dict with error information.
        """
        result: dict[str, Any] = {
            "error": self.__class__.__name__,
            "message": self.message,
        }
        if self.trace_id:
            result["trace_id"] = self.trace_id
        if self.details:
            result["details"] = self.details
        return result


class ValidationError(GPTTalkerError):
    """Raised when input validation fails."""

    pass


class PolicyViolationError(GPTTalkerError):
    """Raised when a policy check fails."""

    pass


class NodeNotFoundError(GPTTalkerError):
    """Raised when a requested node is not found."""

    pass


class RepoNotFoundError(GPTTalkerError):
    """Raised when a requested repo is not found."""

    pass


class PathTraversalError(GPTTalkerError):
    """Raised when a path traversal attempt is detected."""

    pass


class WriteTargetNotAllowedError(GPTTalkerError):
    """Raised when writing to an unapproved target is attempted."""

    pass


class ServiceNotFoundError(GPTTalkerError):
    """Raised when a requested LLM service is not found."""

    pass


class ServiceUnavailableError(GPTTalkerError):
    """Raised when an LLM service is unavailable."""

    pass


class NodeConnectionError(GPTTalkerError):
    """Raised when connection to a node agent fails."""

    pass


class OperationTimeoutError(GPTTalkerError):
    """Raised when an operation times out."""

    pass


class ConfigurationError(GPTTalkerError):
    """Raised when configuration is invalid or missing."""

    pass


# Exception to HTTP status code mapping
EXCEPTION_STATUS_CODES: dict[type[GPTTalkerError], int] = {
    ValidationError: 400,
    PolicyViolationError: 403,
    PathTraversalError: 400,
    WriteTargetNotAllowedError: 403,
    NodeNotFoundError: 404,
    RepoNotFoundError: 404,
    ServiceNotFoundError: 404,
    ServiceUnavailableError: 503,
    NodeConnectionError: 502,
    OperationTimeoutError: 504,
    ConfigurationError: 500,
    GPTTalkerError: 500,
}


def get_status_code(error: GPTTalkerError) -> int:
    """Get HTTP status code for an exception.

    Args:
        error: The GPTTalkerError instance.

    Returns:
        HTTP status code integer.
    """
    for exc_type, code in EXCEPTION_STATUS_CODES.items():
        if isinstance(error, exc_type):
            return code
    return 500


def error_to_response(error: GPTTalkerError) -> dict[str, Any]:
    """Convert exception to API error response.

    Args:
        error: The GPTTalkerError instance.

    Returns:
        Dict suitable for JSON API response.
    """
    return {
        "error": error.__class__.__name__,
        "message": error.message,
        "trace_id": error.trace_id,
        "details": error.details,
    }

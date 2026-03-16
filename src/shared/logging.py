"""Structured logging setup for GPTTalker."""

import json
import logging
import os
import sys
from datetime import UTC, datetime
from typing import Any

from src.shared.context import get_trace_context, get_trace_id

# Sensitive field patterns that should be redacted
SENSITIVE_PATTERNS = {
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "authorization",
    "auth",
    "credential",
    "private_key",
    "access_token",
    "refresh_token",
}


def redact_sensitive(data: Any, _depth: int = 0) -> Any:
    """Redact sensitive fields from log data.

    Recursively processes dicts, lists, and other types to redact
    fields that match known sensitive patterns.

    Args:
        data: The data to redact sensitive info from.
        _depth: Internal recursion depth counter.

    Returns:
        Data with sensitive fields redacted.
    """
    # Prevent infinite recursion
    if _depth > 20:
        return "[MAX_DEPTH_EXCEEDED]"

    if isinstance(data, dict):
        redacted: dict[str, Any] = {}
        for key, value in data.items():
            key_lower = key.lower()
            if any(pattern in key_lower for pattern in SENSITIVE_PATTERNS):
                redacted[key] = "[REDACTED]"
            else:
                redacted[key] = redact_sensitive(value, _depth + 1)
        return redacted
    elif isinstance(data, list):
        return [redact_sensitive(item, _depth + 1) for item in data]
    elif isinstance(data, str):
        # Truncate very long strings
        if len(data) > 10000:
            return data[:10000] + "...[TRUNCATED]"
        return data
    else:
        return data


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging.

    Formats log records as JSON with:
    - timestamp
    - level
    - logger name
    - message
    - trace_id (if available)
    - context (if available)
    - extra fields
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: The log record to format.

        Returns:
            JSON string representation of the log record.
        """
        # Build base log data
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add trace_id if available
        trace_id = get_trace_id()
        if trace_id:
            log_data["trace_id"] = trace_id

        # Add trace context if available
        trace_context = get_trace_context()
        if trace_context:
            log_data["context"] = redact_sensitive(trace_context)

        # Add extra fields from the record
        if hasattr(record, "extra_fields"):
            log_data["extra"] = redact_sensitive(record.extra_fields)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Redact any sensitive data
        log_data = redact_sensitive(log_data)

        return json.dumps(log_data, default=str)


class TextFormatter(logging.Formatter):
    """Human-readable text formatter with structured hints."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as text.

        Args:
            record: The log record to format.

        Returns:
            Formatted text string.
        """
        # Get trace_id if available
        trace_id = get_trace_id()
        trace_part = f" [{trace_id}]" if trace_id else ""

        # Get context if available
        trace_context = get_trace_context()
        context_part = ""
        if trace_context:
            context_parts = [f"{k}={v}" for k, v in list(trace_context.items())[:3]]
            context_part = f" [{', '.join(context_parts)}]"

        # Build format string
        base = f"%(asctime)s - %(name)s - %(levelname)s{trace_part}%(message)s{context_part}"

        formatter = logging.Formatter(base)
        return formatter.format(record)


def setup_logging(
    level: str = "INFO",
    format_type: str = "json",
    log_level_env: str | None = None,
) -> None:
    """Configure structured logging for GPTTalker.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        format_type: Format type ("json" or "text").
        log_level_env: Optional environment variable name to read level from.
    """
    # Get level from env if specified
    if log_level_env and os.environ.get(log_level_env):
        level = os.environ[log_level_env]

    log_level = getattr(logging, level.upper(), logging.INFO)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create appropriate formatter
    if format_type.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()

    # Add handler with formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger for the given name.

    Args:
        name: Logger name (typically __name__).

    Returns:
        Configured logger instance.
    """
    return logging.getLogger(name)


class StructuredLogger:
    """Structured logger with trace_id support and context enrichment.

    Provides methods for logging at different levels with automatic
    trace ID and context propagation.
    """

    def __init__(self, name: str, include_caller: bool = True):
        """Initialize structured logger.

        Args:
            name: Logger name (typically __name__).
            include_caller: Whether to include caller info in logs.
        """
        self.logger = logging.getLogger(name)
        self._context: dict[str, Any] = {}
        self._include_caller = include_caller

    def set_context(self, **kwargs: Any) -> None:
        """Set context fields for subsequent log entries.

        Args:
            **kwargs: Context key-value pairs to add.
        """
        self._context.update(kwargs)

    def clear_context(self) -> None:
        """Clear all context fields."""
        self._context.clear()

    def _build_extra(self, **kwargs: Any) -> dict[str, Any]:
        """Build extra dict with context and kwargs.

        Args:
            **kwargs: Additional kwargs for this call.

        Returns:
            Dict with combined context and kwargs.
        """
        extra = {**self._context, **kwargs}

        # Add caller info if requested
        if self._include_caller:
            import inspect

            try:
                frame = inspect.currentframe()
                if frame:
                    caller = frame.f_back
                    if caller:
                        extra["caller"] = {
                            "function": caller.f_code.co_name,
                            "file": caller.f_code.co_filename,
                            "line": caller.f_lineno,
                        }
            except Exception:
                pass

        return extra

    def _log(self, level: int, message: str, **kwargs: Any) -> None:
        """Internal log method.

        Args:
            level: Logging level (e.g., logging.INFO).
            message: Log message.
            **kwargs: Additional context.
        """
        extra = self._build_extra(**kwargs)
        self.logger.log(level, message, extra={"extra_fields": extra})

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message with context.

        Args:
            message: Log message.
            **kwargs: Additional context.
        """
        self._log(logging.INFO, message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message with context.

        Args:
            message: Log message.
            **kwargs: Additional context.
        """
        self._log(logging.ERROR, message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message with context.

        Args:
            message: Log message.
            **kwargs: Additional context.
        """
        self._log(logging.WARNING, message, **kwargs)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message with context.

        Args:
            message: Log message.
            **kwargs: Additional context.
        """
        self._log(logging.DEBUG, message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message with context.

        Args:
            message: Log message.
            **kwargs: Additional context.
        """
        self._log(logging.CRITICAL, message, **kwargs)

    def exception(self, message: str, **kwargs: Any) -> None:
        """Log exception with traceback.

        Args:
            message: Log message.
            **kwargs: Additional context.
        """
        self._log(logging.ERROR, message, **kwargs)
        self.logger.exception(message)


def create_logger(name: str) -> StructuredLogger:
    """Create a structured logger instance.

    Args:
        name: Logger name (typically __name__).

    Returns:
        Configured StructuredLogger instance.
    """
    return StructuredLogger(name)

"""Tests for structured logging."""

import json
import logging

import pytest

from src.shared.context import (
    TraceContext,
    clear_trace_context,
    clear_trace_id,
    generate_trace_id,
    get_trace_context,
    get_trace_id,
    set_trace_context,
    set_trace_id,
    trace_context,
    trace_context_async,
)
from src.shared.logging import (
    JSONFormatter,
    TextFormatter,
    redact_sensitive,
    setup_logging,
)


# =============================================================================
# Happy-path tests
# =============================================================================


def test_redact_sensitive_dict():
    """Test redacting password/secret/token fields."""
    data = {
        "username": "john",
        "password": "secret123",
        "api_key": "key-abc",
        "action": "login",
    }

    result = redact_sensitive(data)

    assert result["username"] == "john"
    assert result["password"] == "[REDACTED]"
    assert result["api_key"] == "[REDACTED]"
    assert result["action"] == "login"


def test_redact_sensitive_nested():
    """Test redacting nested sensitive fields."""
    data = {
        "user": {
            "name": "john",
            "credentials": {
                "password": "secret",
                "token": "abc123",
            },
        },
        "action": "login",
    }

    result = redact_sensitive(data)

    assert result["user"]["name"] == "john"
    assert result["user"]["credentials"]["password"] == "[REDACTED]"
    assert result["user"]["credentials"]["token"] == "[REDACTED]"
    assert result["action"] == "login"


def test_redact_sensitive_list():
    """Test redacting in lists."""
    data = {
        "users": [
            {"name": "alice", "password": "secret1"},
            {"name": "bob", "password": "secret2"},
        ],
        "tokens": ["token1", "token2"],
    }

    result = redact_sensitive(data)

    assert result["users"][0]["password"] == "[REDACTED]"
    assert result["users"][1]["password"] == "[REDACTED]"
    assert result["tokens"][0] == "[REDACTED]"
    assert result["tokens"][1] == "[REDACTED]"


def test_redact_sensitive_no_match():
    """Test passing through non-sensitive data."""
    data = {
        "username": "john",
        "action": "read",
        "file_path": "/tmp/test.txt",
        "count": 42,
    }

    result = redact_sensitive(data)

    assert result["username"] == "john"
    assert result["action"] == "read"
    assert result["file_path"] == "/tmp/test.txt"
    assert result["count"] == 42


def test_redact_sensitive_long_string():
    """Test truncating very long strings."""
    long_string = "x" * 15000
    data = {"content": long_string}

    result = redact_sensitive(data)

    assert len(result["content"]) < 15000
    assert result["content"].endswith("... [TRUNCATED]")


def test_structured_logger_info():
    """Test logging with context."""
    from src.shared.logging import StructuredLogger

    logger = StructuredLogger("test")
    logger.set_context(user="alice", request_id="123")

    # Should not raise
    logger.info("Test message", extra="data")


def test_structured_logger_error():
    """Test logging errors with context."""
    from src.shared.logging import StructuredLogger

    logger = StructuredLogger("test")
    logger.set_context(user="alice")

    # Should not raise
    logger.error("Error occurred", error_code=500)


def test_structured_logger_set_context():
    """Test setting context for multiple logs."""
    from src.shared.logging import StructuredLogger

    logger = StructuredLogger("test")
    logger.set_context(request_id="abc")
    logger.set_context(user="bob")

    # Context should have both
    assert logger._context["request_id"] == "abc"
    assert logger._context["user"] == "bob"


def test_structured_logger_clear_context():
    """Test clearing context."""
    from src.shared.logging import StructuredLogger

    logger = StructuredLogger("test")
    logger.set_context(request_id="abc")
    logger.clear_context()

    assert len(logger._context) == 0


def test_trace_id_get_set():
    """Test getting and setting trace ID."""
    # Clear first
    clear_trace_id()

    # Initially None
    assert get_trace_id() is None

    # Set trace ID
    set_trace_id("test-trace-123")
    assert get_trace_id() == "test-trace-123"

    # Clear
    clear_trace_id()
    assert get_trace_id() is None


def test_trace_id_generate():
    """Test generating new trace ID."""
    trace_id = generate_trace_id()

    assert trace_id.startswith("trace-")
    assert len(trace_id) > 6


def test_trace_context_sync():
    """Test sync context manager."""
    # Clear first
    clear_trace_id()
    clear_trace_context()

    with trace_context("sync-trace", user="alice") as tid:
        assert tid == "sync-trace"
        assert get_trace_id() == "sync-trace"
        assert get_trace_context() == {"user": "alice"}

    # Should be cleared after exit
    assert get_trace_id() is None


@pytest.mark.asyncio
async def test_trace_context_async():
    """Test async context manager."""
    # Clear first
    clear_trace_id()
    clear_trace_context()

    async with trace_context_async("async-trace", request="test") as tid:
        assert tid == "async-trace"
        assert get_trace_id() == "async-trace"
        assert get_trace_context() == {"request": "test"}

    # Should be cleared after exit
    assert get_trace_id() is None


@pytest.mark.asyncio
async def test_trace_context_propagates_across_async():
    """Test propagating trace context across await."""
    clear_trace_id()
    clear_trace_context()

    async def inner_function():
        # Should still have trace ID from outer context
        return get_trace_id()

    async with trace_context_async("propagate-trace"):
        result = await inner_function()
        assert result == "propagate-trace"


def test_trace_context_class():
    """Test TraceContext class usage."""
    # Clear first
    clear_trace_id()
    clear_trace_context()

    with TraceContext("class-trace", action="test") as tid:
        assert tid == "class-trace"
        assert get_trace_id() == "class-trace"

    # Should be cleared
    assert get_trace_id() is None


def test_json_formatter_includes_trace_id():
    """Test that JSON formatter includes trace ID."""
    clear_trace_id()
    set_trace_id("json-trace-123")

    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None,
    )

    output = formatter.format(record)
    parsed = json.loads(output)

    assert parsed["trace_id"] == "json-trace-123"


def test_text_formatter_includes_trace_id():
    """Test that text formatter includes trace ID."""
    clear_trace_id()
    set_trace_id("text-trace-456")

    formatter = TextFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None,
    )

    output = formatter.format(record)

    assert "text-trace-456" in output


# =============================================================================
# Error-path tests
# =============================================================================


def test_redact_sensitive_max_depth():
    """Test handling deep nesting gracefully."""
    # Create deeply nested structure
    data = {"level1": {"level2": {"level3": {"level4": {"level5": {"value": "deep"}}}}}}

    # Should not raise, should return max depth message
    result = redact_sensitive(data, _depth=20)
    assert result == "[MAX_DEPTH_EXCEEDED]"


def test_trace_context_restores_on_error():
    """Test restoring state after exception."""
    # Clear first
    clear_trace_id()
    clear_trace_context()

    original_trace_id = "original-trace"
    set_trace_id(original_trace_id)

    try:
        with trace_context("new-trace"):
            assert get_trace_id() == "new-trace"
            raise ValueError("Test exception")
    except ValueError:
        pass

    # Should restore original
    assert get_trace_id() == original_trace_id

"""Trace-ID propagation using contextvars."""

import contextlib
import uuid
from contextvars import ContextVar
from typing import Any

# Context variable for trace ID propagation across async boundaries
trace_id_var: ContextVar[str | None] = ContextVar("trace_id", default=None)

# Context variable for additional trace metadata
trace_context_var: ContextVar[dict[str, Any]] = ContextVar("trace_context", default=None)


def get_trace_id() -> str | None:
    """Get the current trace ID from context.

    Returns:
        The current trace ID or None if not set.
    """
    return trace_id_var.get()


def set_trace_id(trace_id: str) -> None:
    """Set the trace ID in context.

    Args:
        trace_id: The trace ID to set.
    """
    trace_id_var.set(trace_id)


def clear_trace_id() -> None:
    """Clear the trace ID from context."""
    trace_id_var.set(None)


def generate_trace_id() -> str:
    """Generate a new unique trace ID.

    Returns:
        A new UUID-based trace ID.
    """
    return f"trace-{uuid.uuid4().hex[:16]}"


def get_trace_context() -> dict[str, Any] | None:
    """Get the current trace context.

    Returns:
        The current trace context dict or None if not set.
    """
    return trace_context_var.get()


def set_trace_context(context: dict[str, Any]) -> None:
    """Set the trace context.

    Args:
        context: The context dict to set.
    """
    trace_context_var.set(context)


def update_trace_context(**kwargs: Any) -> None:
    """Update the trace context with additional fields.

    Args:
        **kwargs: Key-value pairs to add to the context.
    """
    current = trace_context_var.get()
    if current is None:
        current = {}
        trace_context_var.set(current)
    current.update(kwargs)


def clear_trace_context() -> None:
    """Clear the trace context."""
    trace_context_var.set(None)


@contextlib.contextmanager
def trace_context(trace_id: str | None = None, **initial_context: Any):
    """Context manager for trace ID and context propagation.

    This context manager works for both sync and async usage:
    1. Generates a new trace ID if none provided
    2. Sets the trace ID in the context var
    3. Sets initial context values
    4. Cleans up on exit

    Args:
        trace_id: Optional existing trace ID to use. If None, generates new one.
        **initial_context: Initial context key-value pairs.

    Yields:
        The trace ID being used.
    """
    # Generate trace ID if not provided
    tid = trace_id if trace_id else generate_trace_id()

    # Save current state
    old_trace_id = trace_id_var.get()
    old_context = trace_context_var.get()

    try:
        # Set new trace ID and context
        trace_id_var.set(tid)
        trace_context_var.set(initial_context)

        yield tid
    finally:
        # Restore previous state
        trace_id_var.set(old_trace_id)
        trace_context_var.set(old_context)


@contextlib.asynccontextmanager
async def trace_context_async(trace_id: str | None = None, **initial_context: Any):
    """Async context manager for trace ID and context propagation.

    This async context manager:
    1. Generates a new trace ID if none provided
    2. Sets the trace ID in the context var
    3. Sets initial context values
    4. Cleans up on exit

    Args:
        trace_id: Optional existing trace ID to use. If None, generates new one.
        **initial_context: Initial context key-value pairs.

    Yields:
        The trace ID being used.
    """
    # Generate trace ID if not provided
    tid = trace_id if trace_id else generate_trace_id()

    # Save current state
    old_trace_id = trace_id_var.get()
    old_context = trace_context_var.get()

    try:
        # Set new trace ID and context
        trace_id_var.set(tid)
        trace_context_var.set(initial_context)

        yield tid
    finally:
        # Restore previous state
        trace_id_var.set(old_trace_id)
        trace_context_var.set(old_context)


class TraceContext:
    """Helper class for managing trace context.

    Can be used as a context manager or with manual begin/end.
    """

    def __init__(self, trace_id: str | None = None, **initial_context: Any):
        """Initialize trace context.

        Args:
            trace_id: Optional existing trace ID to use.
            **initial_context: Initial context key-value pairs.
        """
        self._trace_id = trace_id
        self._initial_context = initial_context
        self._old_trace_id: str | None = None
        self._old_context: dict[str, Any] | None = None

    def __enter__(self) -> str:
        """Enter context and set trace ID."""
        self._trace_id = self._trace_id if self._trace_id else generate_trace_id()
        self._old_trace_id = trace_id_var.get()
        self._old_context = trace_context_var.get()

        trace_id_var.set(self._trace_id)
        trace_context_var.set(self._initial_context)

        return self._trace_id

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context and restore previous state."""
        trace_id_var.set(self._old_trace_id)
        trace_context_var.set(self._old_context)

    async def __aenter__(self) -> str:
        """Async enter context."""
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async exit context."""
        self.__exit__(exc_type, exc_val, exc_tb)

    @property
    def trace_id(self) -> str | None:
        """Get the current trace ID."""
        return self._trace_id

    @property
    def context(self) -> dict[str, Any]:
        """Get current trace context."""
        return trace_context_var.get() or {}

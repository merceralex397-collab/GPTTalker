"""FastAPI exception handlers and middleware."""

from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.shared.context import get_trace_id
from src.shared.exceptions import GPTTalkerError, get_status_code


class ErrorResponse(BaseModel):
    """Structured error response model."""

    error: str = "InternalServerError"
    message: str = "An unexpected error occurred"
    trace_id: str | None = None
    details: dict[str, Any] | None = None


async def gpttalker_exception_handler(
    request: Request,
    exc: GPTTalkerError,
) -> JSONResponse:
    """Handle GPTTalkerError exceptions.

    Converts GPTTalkerError exceptions to structured JSON responses
    with appropriate status codes and error details.

    Args:
        request: The incoming request.
        exc: The exception to handle.

    Returns:
        JSONResponse with error details.
    """
    # Get trace_id from exception or request context
    trace_id = exc.trace_id or get_trace_id()

    # Get appropriate status code
    status_code = get_status_code(exc)

    # Build error response
    response = ErrorResponse(
        error=exc.__class__.__name__,
        message=exc.message,
        trace_id=trace_id,
        details=exc.details if exc.details else None,
    )

    return JSONResponse(
        status_code=status_code,
        content=response.model_dump(exclude_none=True),
    )


async def validation_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle Pydantic validation errors.

    Converts validation errors to structured JSON responses.

    Args:
        request: The incoming request.
        exc: The validation exception.

    Returns:
        JSONResponse with validation error details.
    """
    trace_id = get_trace_id()

    # Extract validation error details
    details: dict[str, Any] = {}
    if hasattr(exc, "errors"):
        details["validation_errors"] = exc.errors()
    if hasattr(exc, "model"):
        details["model"] = exc.model.__name__

    response = ErrorResponse(
        error="ValidationError",
        message=str(exc),
        trace_id=trace_id,
        details=details,
    )

    return JSONResponse(
        status_code=422,
        content=response.model_dump(exclude_none=True),
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle generic exceptions.

    Catches any unhandled exceptions and returns a generic error response
    without leaking internal error details.

    Args:
        request: The incoming request.
        exc: The exception to handle.

    Returns:
        JSONResponse with generic error details.
    """
    trace_id = get_trace_id()

    # Log the actual exception internally but don't expose to client
    import logging

    logging.getLogger("gpttalker").exception(
        f"Unhandled exception: {exc}",
        extra={"path": str(request.url), "method": request.method},
    )

    response = ErrorResponse(
        error="InternalServerError",
        message="An unexpected error occurred",
        trace_id=trace_id,
    )

    return JSONResponse(
        status_code=500,
        content=response.model_dump(exclude_none=True),
    )


def setup_middleware(app) -> None:
    """Set up exception handlers for a FastAPI app.

    Args:
        app: FastAPI application instance.
    """

    # Import after checking app type
    from pydantic import ValidationError as PydanticValidationError

    # Add exception handlers
    app.add_exception_handler(GPTTalkerError, gpttalker_exception_handler)
    app.add_exception_handler(PydanticValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

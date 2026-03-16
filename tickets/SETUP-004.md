# SETUP-004: Logging and error handling

## Summary

Implement structured logging using structlog across the hub application. Add request/response logging middleware for all HTTP interactions, trace ID generation and propagation for end-to-end request tracing, and standardized error response models. This establishes the observability foundation used by all subsequent features.

## Stage

planning

## Status

todo

## Depends On

- SETUP-002

## Acceptance Criteria

- [ ] structlog configured with JSON output for production, console output for development
- [ ] Trace ID generated per request and included in all log entries
- [ ] Request/response logging middleware captures method, path, status, duration
- [ ] Trace ID propagated via request state and returned in response headers
- [ ] Standard error response model: {"error": str, "detail": str, "trace_id": str}
- [ ] Unhandled exception handler returns structured error response
- [ ] Log level configurable via config file
- [ ] Sensitive data (auth tokens, file contents) excluded from logs

## Artifacts

- None yet

## Notes

- Use structlog processors for trace ID injection
- Middleware should be lightweight — avoid logging large request/response bodies
- Consider adding a correlation ID for multi-step operations spanning hub → node

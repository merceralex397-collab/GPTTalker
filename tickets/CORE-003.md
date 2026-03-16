# CORE-003: Hub-to-node connectivity layer

## Summary

Build the async HTTP client layer that enables the hub to communicate with node agents over the Tailscale network. Implement connection pooling via httpx, Tailscale address resolution, configurable timeouts, and resilience patterns including retry with exponential backoff and circuit-breaker to prevent cascading failures when nodes go offline.

## Stage

planning

## Status

todo

## Depends On

- CORE-001
- CORE-002

## Acceptance Criteria

- [ ] Async httpx client wrapper with connection pooling
- [ ] Node address resolution from registry (tailscale_ip + port)
- [ ] Configurable per-request and connection timeouts
- [ ] Retry logic with exponential backoff for transient failures
- [ ] Circuit-breaker pattern: mark node degraded after N consecutive failures
- [ ] Circuit-breaker recovery: re-check after configurable cooldown
- [ ] Request/response logging with trace ID forwarding
- [ ] Connection error types mapped to structured hub errors
- [ ] Unit tests with mocked httpx responses

## Artifacts

- None yet

## Notes

- httpx.AsyncClient should be shared across requests (connection pooling)
- Circuit-breaker state can be in-memory (resets on hub restart is acceptable)
- Forward trace_id as X-Trace-ID header to node agents
- Consider a NodeClient class that encapsulates all communication with a specific node

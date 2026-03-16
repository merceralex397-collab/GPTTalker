# POLISH-001: Error handling hardening

## Summary

Harden error handling across all MCP tools and hub/node communication paths. Implement comprehensive error responses for every known failure mode: node offline, repo alias not found, context degraded, LLM timeout, write target validation failure, etc. Every error should return a structured response with trace ID and actionable information.

## Stage

planning

## Status

blocked

## Depends On

- CORE-007
- REPO-001
- LLM-001
- CTX-003

## Acceptance Criteria

- [ ] Error catalog: documented list of all error types with codes
- [ ] Every MCP tool returns structured errors (never raw 500s)
- [ ] Node offline: clear message with node name and last_seen timestamp
- [ ] Repo not found: suggestion of similar repo aliases
- [ ] Context degraded: partial results with quality indicator
- [ ] LLM timeout: timeout duration, backend name, retry suggestion
- [ ] Write validation failure: specific reason (extension, path, target)
- [ ] All errors include trace_id for correlation
- [ ] Error responses tested for every failure path
- [ ] Error documentation for ChatGPT (what each error means and what to do)

## Artifacts

- None yet

## Notes

- This ticket is intentionally late in the sequence — it hardens existing tools
- Error messages should be ChatGPT-friendly: clear, actionable, not technical jargon
- Consider an error code taxonomy: ENODEOFFLINE, EREPOMISSING, ELLMTIMEOUT, etc.
- Trace ID is critical for debugging — must be in every error response

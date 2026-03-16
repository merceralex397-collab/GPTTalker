# POLISH-002: End-to-end integration tests

## Summary

Create comprehensive end-to-end integration tests that exercise the full tool chain: hub receives MCP tool call → routes to node agent → node performs operation → response returned to hub → formatted MCP response. Include security boundary tests and failure mode tests to verify the system behaves correctly under adverse conditions.

## Stage

planning

## Status

blocked

## Depends On

- POLISH-001

## Acceptance Criteria

- [ ] E2E test: inspect_repo_tree through full hub → node → response chain
- [ ] E2E test: read_repo_file with truncation and binary detection
- [ ] E2E test: search_repo with results and empty results
- [ ] E2E test: write_markdown with validation and atomic write
- [ ] E2E test: chat_llm routing to mock LLM backend
- [ ] E2E test: get_project_context with indexed repo
- [ ] Security tests: path traversal attempts rejected at every layer
- [ ] Security tests: unauthorized node/repo access rejected
- [ ] Security tests: write to non-approved target rejected
- [ ] Failure tests: node offline during operation
- [ ] Failure tests: LLM timeout during chat
- [ ] Failure tests: Qdrant unavailable during context retrieval
- [ ] All tests runnable in CI without external services (mocked backends)

## Artifacts

- None yet

## Notes

- Use docker-compose or test fixtures to simulate multi-node setup
- Security tests are critical — these are the guardrails
- Consider property-based testing for path validation (hypothesis library)
- Failure tests should verify graceful degradation, not just error responses

# Planning: POLISH-001

## Ticket
- **ID**: POLISH-001
- **Title**: Contract tests for MCP tools and failure modes
- **Wave**: 6
- **Lane**: qa

## Summary
Build the higher-level contract tests that prove the exposed GPTTalker tools behave correctly under expected and failure-path scenarios.

## Acceptance Criteria
1. Tool contracts are covered by tests
2. Failure-mode tests are explicit
3. Validation remains aligned with the canonical brief

## Dependencies
- REPO-003 (search_repo and git_status tools)
- WRITE-001 (write_markdown tool)
- LLM-002 (chat_llm routing)
- CTX-003 (get_project_context)
- OBS-002 (task detail tools)

## Analysis

### Background
GPTTalker exposes many MCP tools. Contract tests verify:
- Tools return expected response formats
- Parameters are validated correctly
- Failure paths return proper errors
- Policy enforcement works

### Test Categories

1. **Discovery Tools**
   - list_nodes returns nodes with health
   - list_repos returns approved repos

2. **Inspection Tools**
   - inspect_repo_tree validates parameters
   - read_repo_file rejects traversal

3. **Search Tools**
   - search_repo validates patterns
   - git_status returns proper format

4. **Write Tools**
   - write_markdown validates extensions
   - write_markdown enforces write targets

5. **LLM Tools**
   - chat_llm validates service aliases
   - chat_llm returns structured responses

6. **Context Tools**
   - get_project_context validates queries
   - index_repo handles idempotency

7. **Failure Mode Tests**
   - Unknown nodes rejected
   - Unknown repos rejected
   - Invalid paths rejected
   - Missing required params rejected

### Implementation Plan
1. Create test structure under tests/hub/
2. Add contract tests for each tool category
3. Add failure mode tests
4. Run tests to verify

## Validation
- All tool contracts tested
- Failure modes verified

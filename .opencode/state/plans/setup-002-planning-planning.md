# SETUP-002 Implementation Plan: Shared Schemas, Config Loading, and Structured Logging

## Scope

This ticket establishes the foundational shared runtime components used by both the hub and node agents. It covers:

1. **Shared Pydantic Models** — Request/response schemas for hub↔node communication and MCP tool boundaries
2. **Configuration Loading** — Centralized config patterns with validation using pydantic-settings
3. **Structured Logging** — Trace-ID propagation, context enrichment, and secret redaction
4. **Exception Handling** — Structured error responses for FastAPI integration

## Files and Systems Affected

### New Files to Create

| File | Purpose |
|------|---------|
| `src/shared/schemas.py` | Request/response models for hub↔node communication |
| `src/shared/middleware.py` | FastAPI exception handler and structured error responses |
| `src/shared/context.py` | Trace-ID propagation utilities (contextvars) |

### Files to Modify

| File | Current State | Changes Required |
|------|---------------|-------------------|
| `src/shared/models.py` | Skeleton with TODOs | Complete NodeInfo, RepoInfo, WriteTargetInfo, LLMServiceInfo, TaskRecord, IssueRecord; add MCP tool models |
| `src/shared/config.py` | Basic SharedConfig | Add config validation, environment-specific patterns, nested config support |
| `src/shared/logging.py` | Basic StructuredLogger | Full implementation with JSON output, trace_id, redaction, context propagation |
| `src/shared/exceptions.py` | Exception classes exist | Add exception-to-response mapping, FastAPI error handler integration |
| `src/hub/config.py` | Basic HubConfig | Add validation, required vs optional field distinction, nested settings |
| `src/node_agent/config.py` | Basic NodeAgentConfig | Add validation, path normalization at startup |

### Dependencies

The following are already in `pyproject.toml`:
- `pydantic>=2.5.0`
- `pydantic-settings>=2.1.0`

No new dependencies required. The plan uses Python's built-in `contextvars` for trace-ID propagation.

---

## Implementation Steps

### Step 1: Complete Shared Models (`src/shared/models.py`)

**Goal**: Finalize all registry and record models with proper validation.

**Actions**:
1. Add field validation to `NodeInfo`:
   - `status` must be one of: `unknown`, `healthy`, `unhealthy`, `offline`
   - `node_id` must match pattern `^[a-zA-Z0-9_-]+$`

2. Add field validation to `RepoInfo`:
   - `path` must be a valid absolute path
   - `is_indexed` defaults to `False`

3. Add field validation to `WriteTargetInfo`:
   - `allowed_extensions` must start with `.`
   - `target_id` must match pattern `^[a-zA-Z0-9_-]+$`

4. Add field validation to `LLMServiceInfo`:
   - `type` must be one of: `opencode`, `llama`, `embedding`, `helper`
   - `api_key` must not be logged (handled by redaction)

5. Enhance `TaskRecord`:
   - `outcome` must be one of: `success`, `error`, `timeout`, `rejected`
   - Add `started_at: datetime` field for duration calculation

6. Enhance `IssueRecord`:
   - `status` must be one of: `open`, `in_progress`, `resolved`, `wontfix`

### Step 2: Create Hub↔Node Communication Schemas (`src/shared/schemas.py`)

**Goal**: Define request/response models for tool calls across the hub↔node boundary.

**Actions**:
1. Create `ToolRequest` model
2. Create `ToolResponse` model
3. Create `NodeHealthStatus` model
4. Create `RepoTreeResponse` model for directory listing
5. Create `FileContentResponse` model

### Step 3: Implement Trace-ID Propagation (`src/shared/context.py`)

**Goal**: Provide contextvars-based trace-ID storage that propagates across async boundaries.

### Step 4: Enhance Configuration Loading

**Goal**: Add validation, required/optional distinction, and environment-specific patterns.

### Step 5: Implement Full Structured Logging

**Goal**: Complete the StructuredLogger with JSON output, trace-ID support, and secret redaction.

### Step 6: Add Exception Handling Middleware

**Goal**: Provide FastAPI exception handlers that return structured error responses.

---

## Validation Plan

Run validation commands to verify implementation.

---

## Acceptance Criteria

- [ ] Shared request/response models defined in `src/shared/schemas.py`
- [ ] Registry models complete with proper validation
- [ ] Configuration pattern defined with pydantic-settings
- [ ] Structured logging with trace-ID and redaction
- [ ] Trace-ID propagation using contextvars
- [ ] Exception handling middleware

---

## No Blockers

All required decisions are resolved.
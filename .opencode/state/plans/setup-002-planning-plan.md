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
1. Create `ToolRequest` model:
   ```python
   class ToolRequest(BaseModel):
       tool_name: str
       parameters: dict[str, Any]
       trace_id: str
       caller: str
       target_node: str | None = None
       target_repo: str | None = None
   ```

2. Create `ToolResponse` model:
   ```python
   class ToolResponse(BaseModel):
       trace_id: str
       outcome: str  # success, error
       result: Any | None = None
       error: str | None = None
       duration_ms: int
   ```

3. Create `NodeHealthStatus` model:
   ```python
   class NodeHealthStatus(BaseModel):
       node_id: str
       status: str
       last_seen: datetime
       checks: dict[str, bool] = {}
   ```

4. Create `RepoTreeResponse` model for directory listing:
   ```python
   class RepoTreeResponse(BaseModel):
       repo_id: str
       path: str
       entries: list[TreeEntry]
       total_files: int
   ```

5. Create `FileContentResponse` model:
   ```python
   class FileContentResponse(BaseModel):
       repo_id: str
       path: str
       content: str
       encoding: str
       size_bytes: int
       truncated: bool = False
   ```

### Step 3: Implement Trace-ID Propagation (`src/shared/context.py`)

**Goal**: Provide contextvars-based trace-ID storage that propagates across async boundaries.

**Actions**:
1. Create `trace_id_var` using `contextvars.ContextVar`:
   ```python
   from contextvars import ContextVar
   trace_id_var: ContextVar[str | None] = ContextVar("trace_id", default=None)
   ```

2. Implement helper functions:
   - `get_trace_id() -> str | None`
   - `set_trace_id(trace_id: str) -> ContextVar.set`
   - `clear_trace_id() -> None`
   - `generate_trace_id() -> str` (use UUID4)

3. Create `TraceContext` manager class for `async with` usage:
   ```python
   @asynccontextmanager
   async def trace_context(trace_id: str | None = None):
       tid = trace_id or generate_trace_id()
       token = trace_id_var.set(tid)
       try:
           yield tid
       finally:
           trace_id_var.reset(token)
   ```

### Step 4: Enhance Configuration Loading (`src/shared/config.py` and domain configs)

**Goal**: Add validation, required/optional distinction, and environment-specific patterns.

**Actions**:

1. Update `SharedConfig`:
   - Add `model_config = SettingsConfigDict(env_prefix="GPTTALKER_", extra="ignore")`
   - Add `__init__` validation that logs warning for unknown env vars (instead of allowing them)
   - Add `_validate_settings()` method for cross-field validation

2. Add configuration validators:
   ```python
   @field_validator("log_level")
   @classmethod
   def validate_log_level(cls, v: str) -> str:
       valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
       if v.upper() not in valid_levels:
           raise ValueError(f"log_level must be one of {valid_levels}")
       return v.upper()
   ```

3. Update `HubConfig`:
   - Add validators for `port` (1-65535)
   - Add validators for `database_url` (must be valid SQLite path or URL)
   - Add `model_config` with proper settings
   - Add `_check_required_settings()` for mandatory fields in production

4. Update `NodeAgentConfig`:
   - Add path validation at startup for `allowed_repos` and `allowed_write_targets`
   - Add `validate_allowed_paths()` method that runs on config load
   - Ensure `hub_url` is a valid URL format

5. Add config loading utilities:
   ```python
   def load_config(config_class: type[BaseSettings]) -> BaseSettings:
       """Load and validate configuration."""
       try:
           return config_class()
       except ValidationError as e:
           raise ConfigurationError(f"Config validation failed: {e}") from e
   ```

### Step 5: Implement Full Structured Logging (`src/shared/logging.py`)

**Goal**: Complete the StructuredLogger with JSON output, trace-ID support, and secret redaction.

**Actions**:

1. Add redaction utilities:
   ```python
   REDACTED = "[REDACTED]"
   
   SENSITIVE_KEYS = {
       "api_key", "token", "password", "secret", "private_key",
       "access_token", "refresh_token", "bearer_token", "auth",
   }
   
   def redact_sensitive(data: dict[str, Any]) -> dict[str, Any]:
       """Recursively redact sensitive fields from a dictionary."""
       if not isinstance(data, dict):
           return data
       result = {}
       for k, v in data.items():
           if any(s in k.lower() for s in SENSITIVE_KEYS):
               result[k] = REDACTED
           elif isinstance(v, dict):
               result[k] = redact_sensitive(v)
           elif isinstance(v, list):
               result[k] = [redact_sensitive(i) if isinstance(i, dict) else i for i in v]
           else:
               result[k] = v
       return result
   ```

2. Enhance `StructuredLogger`:
   - Add `trace_id` parameter to all log methods
   - Implement JSON format output using `json.dumps` with `default=str`
   - Include all canonical brief fields: `trace_id`, `tool_name`, `target_node`, `target_repo`, `caller`, `outcome`, `duration_ms`
   - Add `log_tool_call()` and `log_tool_result()` convenience methods

3. Add JSON logging setup:
   ```python
   class JSONFormatter(logging.Formatter):
       """JSON formatter for structured logging."""
       
       def format(self, record: logging.LogRecord) -> str:
           log_data = {
               "timestamp": self.formatTime(record),
               "level": record.levelname,
               "logger": record.name,
               "message": record.getMessage(),
               "module": record.module,
               "function": record.funcName,
               "line": record.lineno,
           }
           # Add extra fields from context
           for key in ("trace_id", "tool_name", "target_node", "target_repo", 
                       "caller", "outcome", "duration_ms"):
               if hasattr(record, key):
                   log_data[key] = getattr(record, key)
           
           return json.dumps(redact_sensitive(log_data))
   ```

4. Update `setup_logging()`:
   - Accept `log_level`, `format_type`, and optional `output_file`
   - Install `JSONFormatter` when `format_type == "json"`
   - Set up logging handlers for both stdout and optional file

5. Add log correlation decorator:
   ```python
   def log_correlation(func):
       """Decorator to automatically add trace_id to log context."""
       @functools.wraps(func)
       async def async_wrapper(*args, **kwargs):
           trace_id = get_trace_id() or generate_trace_id()
           token = trace_id_var.set(trace_id)
           try:
               return await func(*args, **kwargs)
           finally:
               trace_id_var.reset(token)
       return async_wrapper
   ```

### Step 6: Add Exception Handling Middleware (`src/shared/middleware.py` and `src/shared/exceptions.py`)

**Goal**: Provide FastAPI exception handlers that return structured error responses.

**Actions**:

1. Create `ErrorResponse` model:
   ```python
   class ErrorResponse(BaseModel):
       error: str
       error_type: str
       trace_id: str | None
       detail: str | None = None
   ```

2. Update exception classes to include `trace_id` support:
   - Add optional `trace_id` parameter to each exception
   - Add `__str__` methods that include context

3. Create FastAPI exception handlers in `src/shared/middleware.py`:
   ```python
   from fastapi import Request, status
   from fastapi.responses import JSONResponse
   
   async def gpttalker_exception_handler(
       request: Request, 
       exc: GPTTalkerError
   ) -> JSONResponse:
       trace_id = get_trace_id()
       return JSONResponse(
           status_code=status.HTTP_400_BAD_REQUEST,
           content=ErrorResponse(
               error=str(exc),
               error_type=type(exc).__name__,
               trace_id=trace_id,
           ).model_dump(),
       )
   ```

4. Register handlers in FastAPI app (done in SETUP-004):
   ```python
   app.add_exception_handler(GPTTalkerError, gpttalker_exception_handler)
   ```

---

## Validation Plan

### Code Quality Checks

1. **Linting** (ruff):
   ```bash
   ruff check src/shared/
   ```
   Expected: No errors. Fix any linting issues before proceeding.

2. **Type checking** (ruff is configured, but can add mypy if needed):
   ```bash
   ruff check src/shared/ --select=type
   ```

3. **Import verification**:
   ```bash
   python -c "from src.shared.models import *; from src.shared.config import *; from src.shared.logging import *; from src.shared.exceptions import *; print('All imports OK')"
   ```

### Functional Validation

1. **Config loading test**:
   ```python
   from src.shared.config import SharedConfig, HubConfig
   from src.node_agent.config import NodeAgentConfig
   
   shared = SharedConfig()
   assert shared.log_level in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
   print(f"SharedConfig loaded: log_level={shared.log_level}")
   ```

2. **Structured logging test**:
   ```python
   from src.shared.logging import StructuredLogger, setup_logging, redact_sensitive
   
   setup_logging(level="DEBUG", format_type="json")
   logger = StructuredLogger("test")
   logger.info("Test message", tool_name="test_tool", trace_id="test-123")
   
   # Test redaction
   sensitive_data = {"api_key": "secret123", "password": "pass", "data": "ok"}
   redacted = redact_sensitive(sensitive_data)
   assert redacted["api_key"] == "[REDACTED]"
   assert redacted["password"] == "[REDACTED]"
   assert redacted["data"] == "ok"
   print("Redaction test passed")
   ```

3. **Trace-ID propagation test**:
   ```python
   import asyncio
   from src.shared.context import get_trace_id, set_trace_id, trace_context, generate_trace_id
   
   async def test_trace():
       assert get_trace_id() is None
       async with trace_context("test-trace-123") as tid:
           assert get_trace_id() == "test-trace-123"
           assert tid == "test-trace-123"
       assert get_trace_id() is None
       print("Trace context test passed")
   
   asyncio.run(test_trace())
   ```

4. **Exception handling test**:
   ```python
   from src.shared.exceptions import ValidationError, NodeNotFoundError
   
   try:
       raise NodeNotFoundError("node-123")
   except GPTTalkerError as e:
       assert "node-123" in str(e)
       print(f"Exception test passed: {type(e).__name__}")
   ```

5. **Model validation test**:
   ```python
   from pydantic import ValidationError
   from src.shared.models import NodeInfo, LLMServiceInfo
   
   # Test valid model
   node = NodeInfo(node_id="test-node", name="Test", hostname="test.local")
   assert node.status == "unknown"
   
   # Test invalid status
   try:
       NodeInfo(node_id="test", name="Test", hostname="x", status="invalid")
   except ValidationError:
       print("Model validation test passed")
   ```

---

## Risks and Assumptions

### Risks

1. **Trace-ID in async contexts**: Using `contextvars` works correctly with asyncio, but nested async calls must preserve context. Mitigated by `trace_context` manager.

2. **JSON logging performance**: JSON serialization on every log call has overhead. Mitigated by using `format_type="json"` only when needed; default remains text.

3. **Config validation at import time**: Running validation at module import could fail if env vars aren't set. Mitigated by using lazy validation in `get_*_config()` functions.

### Assumptions

1. **Python 3.11+**: The `str | None` union syntax and `contextvars` are available.
2. **Environment variables**: The operator will set required environment variables; defaults are provided for development only.
3. **Single config instance**: The design assumes a single config instance per process. For testing, use environment variables or direct instantiation.
4. **Tailscale networking**: Node-to-hub communication happens over Tailscale; no special handling needed in logging (just standard HTTP).

---

## Blockers and Required User Decisions

### No Blockers

All required decisions are resolved:

| Decision | Resolution |
|----------|------------|
| Config env prefix | `GPTTALKER_` for shared/hub, `GPTTALKER_NODE_` for node agent |
| Log format | JSON for production, text for development |
| Trace-ID format | UUID4 string |
| Sensitive field detection | Case-insensitive key matching |
| Exception handling | FastAPI JSON responses with structured error format |

### Implementation Order

1. First: Complete models and create schemas (foundation)
2. Second: Add trace-ID context utilities (dependency for logging)
3. Third: Enhance configuration loading
4. Fourth: Complete structured logging with redaction
5. Fifth: Add exception middleware
6. Sixth: Run all validation tests

---

## Acceptance Criteria Checklist

- [ ] **Shared request/response models**: `ToolRequest`, `ToolResponse`, `NodeHealthStatus`, `RepoTreeResponse`, `FileContentResponse` defined in `src/shared/schemas.py`
- [ ] **Registry models complete**: `NodeInfo`, `RepoInfo`, `WriteTargetInfo`, `LLMServiceInfo` have proper validation in `src/shared/models.py`
- [ ] **Record models complete**: `TaskRecord`, `IssueRecord` have proper fields and validation
- [ ] **Configuration pattern defined**: SharedConfig, HubConfig, NodeAgentConfig use pydantic-settings with validation
- [ ] **Environment variable prefixes**: Correctly set (`GPTTALKER_` and `GPTTALKER_NODE_`)
- [ ] **Structured logging**: StructuredLogger outputs JSON with trace_id, tool_name, target_node, target_repo, caller, outcome, duration_ms
- [ ] **Secret redaction**: redact_sensitive() function handles keys containing api_key, token, password, secret, etc.
- [ ] **Trace-ID propagation**: contextvars-based get/set/clear functions work across async boundaries
- [ ] **Exception handling**: GPTTalkerError subclasses provide structured error responses
- [ ] **Validation commands**: All commands in Validation Plan section pass
- [ ] **Logging conventions**: Match canonical brief requirements exactly

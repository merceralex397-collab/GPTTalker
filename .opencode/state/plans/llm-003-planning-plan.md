# Implementation Plan: LLM-003 - Helper-model and embedding-service adapters

## Overview

Ticket LLM-003 adds adapter support for helper-class models and the dedicated embedding service used by the context pipeline. This extends the existing LLM routing infrastructure to support lighter-weight models for quick tasks and the embedding service needed for Qdrant-based context indexing.

## Acceptance Criteria

1. **Helper-model alias routing is defined** — Helper models (lightweight models for quick tasks) are routed with appropriate payload formatting and configuration
2. **Embedding-service adapter contract is explicit** — A dedicated adapter handles embedding requests with specific timeout, batch, and response handling
3. **Timeout and failure behavior is planned** — Each adapter type has explicit timeout configuration and failure handling patterns

## Context

### Existing Infrastructure

- **LLMServiceClient** (`src/hub/services/llm_client.py`): Base HTTP client for LLM services with `chat()` method
- **LLMServiceType enum** (`src/shared/models.py`): Already defines `HELPER` and `EMBEDDING` service types
- **LLMServiceInfo** model: Contains service configuration including type, endpoint, and API key
- **chat_llm_handler** (`src/hub/tools/llm.py`): Main LLM routing handler that validates service and dispatches
- **OpenCodeAdapter** (`src/hub/services/opencode_adapter.py`): Specialized adapter with session support and timeout handling pattern
- **HubConfig** (`src/hub/config.py`): Contains `llm_client_timeout` (120s default)

### What's Missing

1. **Helper model payload builder** — Already exists in LLMServiceClient but may need refinement
2. **Embedding adapter** — No dedicated adapter exists; embedding services have different contracts (text input → vector output, not chat)
3. **Service-type-specific timeouts** — Currently single timeout for all LLM clients
4. **chat_embeddings tool** — No MCP tool exposed for embedding generation

---

## Approach

### 1. Helper-Model Adapter Approach

Helper models are lighter-weight models used for quick tasks (summarization, classification, simple transformations). They typically:

- Accept simpler prompt formats than full chat models
- Have shorter expected response times
- May use different API contracts (some use `/completions`而非 `/chat/completions`)

**Design Decision:** Extend `LLMServiceClient` with helper-specific methods rather than creating a separate adapter class. The existing `_build_helper_payload()` method is a good foundation but needs enhancement.

**Implementation:**
- Add `chat_helper()` method to `LLMServiceClient` with helper-specific payload building
- Support both chat-style and completion-style endpoints
- Use shorter default timeout for helper models (60s vs 120s for full models)
- Add service-type validation to route to correct payload builder

### 2. Embedding-Service Adapter Approach

Embedding services are fundamentally different from chat models:

- Input: Text string or array of strings
- Output: Vector embeddings (array of floats)
- Use case: Semantic search, context indexing, similarity calculations
- Typical API: `/embeddings` endpoint (OpenAI-compatible) or custom

**Design Decision:** Create a dedicated `EmbeddingServiceClient` class similar to `OpenCodeAdapter`. This separation:

- Keeps embedding-specific logic isolated
- Allows different timeout policies (embeddings are typically faster)
- Supports batch embedding requests
- Handles vector response parsing separately

**Implementation:**
- Create `src/hub/services/embedding_client.py` with `EmbeddingServiceClient` class
- Support single and batch embedding requests
- Default timeout: 30 seconds (embeddings are typically fast)
- Return standardized format: `{embeddings: [[float]], model: str, tokens_used: int}`

### 3. Timeout and Failure Behavior

| Service Type | Default Timeout | Timeout Behavior | Failure Response |
|--------------|----------------|------------------|------------------|
| Helper | 60s | Retry once, then fail | `{success: false, error: "timeout", latency_ms: ...}` |
| Embedding | 30s | No retry (idempotent) | `{success: false, error: "timeout", latency_ms: ...}` |
| Chat (existing) | 120s | Configurable | `{success: false, error: "...", latency_ms: ...}` |

**Failure Handling Pattern:**
- All adapters return `{success: boolean, error?: string, latency_ms: number}` on failure
- Structured logging with `latency_ms`, `error_type`, `service_id`
- Timeout exceptions are caught and converted to structured responses
- HTTP errors are logged with status code and converted to structured responses

---

## Integration Points

### With LLMServiceClient

The existing `LLMServiceClient` will be extended:

```python
class LLMServiceClient:
    # Existing methods remain unchanged
    
    async def chat_helper(
        self,
        service: LLMServiceInfo,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        """Send request to helper-model service."""
        # Helper-specific payload building and timeout handling
```

### With Tool Registration

New tool `chat_embeddings` will be added to `src/hub/tools/__init__.py`:

```python
# In register_llm_tools():
from src.hub.tools.embedding import chat_embeddings_handler

registry.register(
    ToolDefinition(
        name="chat_embeddings",
        description="Generate embeddings for text using an approved embedding service...",
        handler=chat_embeddings_handler,
        parameters={...},
        policy=LLM_REQUIREMENT,
    )
)
```

### With Dependencies

Add DI provider for `EmbeddingServiceClient` in `src/hub/dependencies.py`:

```python
async def get_embedding_service_client(request: Request) -> EmbeddingServiceClient:
    """Get embedding service HTTP client."""
    http_client = request.app.state.http_client
    config = request.app.state.config
    return EmbeddingServiceClient(
        http_client=http_client,
        default_timeout=config.embedding_client_timeout,
    )
```

Add `embedding_client_timeout` to `HubConfig` in `src/hub/config.py`.

---

## New Files to Create

| File | Purpose |
|------|---------|
| `src/hub/services/embedding_client.py` | Dedicated client for embedding services with batch support |
| `src/hub/tools/embedding.py` | MCP tool handler for `chat_embeddings` |
| `tests/hub/tools/test_embedding.py` | Unit tests for embedding tool |
| `tests/hub/services/test_embedding_client.py` | Unit tests for embedding client |

---

## Existing Files to Modify

| File | Modification |
|------|--------------|
| `src/hub/config.py` | Add `embedding_client_timeout` field |
| `src/hub/dependencies.py` | Add `get_embedding_service_client` provider |
| `src/hub/tools/__init__.py` | Register `chat_embeddings` tool |
| `src/hub/services/llm_client.py` | Add `chat_helper()` method with timeout handling |

---

## Implementation Steps

### Step 1: Config and DI (15 min)

1. Add `embedding_client_timeout: float = 30.0` to `HubConfig` in `src/hub/config.py`
2. Add `get_embedding_service_client` provider to `src/hub/dependencies.py`

### Step 2: EmbeddingServiceClient (30 min)

3. Create `src/hub/services/embedding_client.py`:
   - Class `EmbeddingServiceClient` with `__init__`, `embed()`, `embed_batch()`
   - `_build_payload()` for OpenAI-compatible `/embeddings` format
   - `_parse_response()` returning `{embeddings: list[list[float]], model: str, tokens_used: int | None}`
   - Timeout and error handling following `OpenCodeAdapter` pattern
   - Proper structured logging

### Step 3: chat_embeddings Tool (20 min)

4. Create `src/hub/tools/embedding.py`:
   - `chat_embeddings_handler()` with service_id/service_name, text, batch support
   - Validation of service type (must be `EMBEDDING`)
   - Response formatting with service metadata

5. Register tool in `src/hub/tools/__init__.py`:
   - Import `chat_embeddings_handler`
   - Add `ToolDefinition` with `LLM_REQUIREMENT` policy
   - Parameters: `service_id | service_name`, `text` (string or array), `encoding_format` (optional)

### Step 4: Helper Model Enhancement (15 min)

6. Enhance `src/hub/services/llm_client.py`:
   - Add `chat_helper()` method with 60s default timeout
   - Support completion-style (`prompt` field) and chat-style (`messages` field) APIs
   - Add explicit failure handling with structured responses

### Step 5: Testing (20 min)

7. Create unit tests:
   - `test_embedding_client_embed()` — single text embedding
   - `test_embedding_client_embed_batch()` — batch embedding
   - `test_embedding_client_timeout()` — timeout handling
   - `test_embedding_client_error()` — HTTP error handling
   - `test_chat_embeddings_handler()` — tool handler with validation

8. Verify existing tests still pass:
   - `make test` or `pytest`

### Step 6: Validation (10 min)

9. Run lint checks:
   - `ruff check src/hub/services/embedding_client.py src/hub/tools/embedding.py`
   - `ruff format --check`

10. Run type checks:
    - `ruff check --select=I src/hub/services/embedding_client.py src/hub/tools/embedding.py`

---

## Validation Plan

### Functional Validation

1. **Embedding client initialization** — Verify `EmbeddingServiceClient` can be created with HTTP client and timeout
2. **Single embedding request** — Mock HTTP response, verify parsing returns correct structure
3. **Batch embedding request** — Verify multiple texts are sent and parsed correctly
4. **Timeout handling** — Verify timeout exception returns `{success: false, error: "timeout"}`
5. **Tool registration** — Verify `chat_embeddings` appears in tool registry
6. **Service type validation** — Verify embedding tool rejects non-EMBEDDING service types

### Integration Validation

1. **DI integration** — Verify `get_embedding_service_client` can be resolved in request context
2. **Policy integration** — Verify `LLM_REQUIREMENT` is applied to `chat_embeddings` tool
3. **Config integration** — Verify `embedding_client_timeout` is read from config

### Code Quality Validation

1. **Type hints** — All new functions and methods have complete type annotations
2. **Docstrings** — All public methods have docstrings following project conventions
3. **Logging** — All operations log with structured format including `service_id`, `latency_ms`
4. **Error handling** — All exceptions are caught and converted to structured responses

---

## Risks and Assumptions

### Risks

1. **Embedding API format variance** — Different embedding services use different request/response formats. The plan assumes OpenAI-compatible format as the default, but may need adapter patterns for other services.
   - **Mitigation**: Make `EmbeddingServiceClient` extensible with custom payload builders

2. **Helper model timeout too aggressive** — 60s may be too short for some helper models on slower hardware.
   - **Mitigation**: Allow timeout override in `chat_helper()` call, keep config-based default

3. **Batch size limits** — Embedding services often have limits on batch size (e.g., 100 texts per request).
   - **Mitigation**: Add batch chunking logic in `embed_batch()` if service supports it

### Assumptions

1. **Embedding service is HTTP-accessible** — Assumes embedding service is reachable directly from hub, not via node agent. If embedding service is on a managed node, additional routing would be needed.
2. **OpenAI-compatible embedding format** — Assumes most embedding services use OpenAI-compatible `/embeddings` endpoint format.
3. **Helper models support specific payload format** — The existing `_build_helper_payload()` is a reasonable starting point but may need adjustment based on actual helper service APIs.

---

## Blocker Status

**No blockers identified.** All required decisions have been made:

- Helper-model routing: Uses existing LLMServiceClient with new `chat_helper()` method
- Embedding adapter: New `EmbeddingServiceClient` class with dedicated timeout (30s)
- Timeout handling: Service-type-specific timeouts with structured failure responses
- Tool registration: New `chat_embeddings` tool with `LLM_REQUIREMENT` policy
- DI integration: Standard pattern with config-based timeout

---

## Acceptance Confirmation

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Helper-model alias routing defined | ✅ | `chat_helper()` method in LLMServiceClient with 60s timeout |
| Embedding-service adapter contract explicit | ✅ | `EmbeddingServiceClient` class with `embed()` and `embed_batch()` |
| Timeout and failure behavior planned | ✅ | Per-service timeouts with structured error responses |

---

## Files Reference

### New Files (4)

- `.opencode/state/plans/llm-003-planning-plan.md` (this file)
- `src/hub/services/embedding_client.py` (new)
- `src/hub/tools/embedding.py` (new)
- `tests/hub/services/test_embedding_client.py` (new)
- `tests/hub/tools/test_embedding.py` (new)

### Modified Files (4)

- `src/hub/config.py` — add `embedding_client_timeout`
- `src/hub/dependencies.py` — add `get_embedding_service_client`
- `src/hub/tools/__init__.py` — register `chat_embeddings` tool
- `src/hub/services/llm_client.py` — add `chat_helper()` method

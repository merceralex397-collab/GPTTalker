# Implementation Summary: LLM-003 - Helper-model and embedding-service adapters

## Overview

Ticket LLM-003 adds adapter support for helper-class models and the dedicated embedding service used by the context pipeline. This extends the existing LLM routing infrastructure to support lighter-weight models for quick tasks and the embedding service needed for Qdrant-based context indexing.

## Changes Made

### New Files Created

1. **`src/hub/services/embedding_client.py`** - EmbeddingServiceClient class
   - Supports single (`embed()`) and batch (`embed_batch()`) embedding requests
   - OpenAI-compatible `/embeddings` endpoint format
   - 30-second default timeout
   - Structured error handling with timeout, HTTP error, and generic exception handling
   - Returns standardized format: `{embeddings: [[float]], model: str, tokens_used: int | None, latency_ms: int}`

2. **`src/hub/tools/embedding.py`** - chat_embeddings tool handler
   - Validates service is of type EMBEDDING
   - Supports single text or batch texts input
   - Validates encoding format (float, base64, int8)
   - Returns embeddings array with model and token metadata

### Files Modified

1. **`src/hub/config.py`** - Added `embedding_client_timeout: float = 30.0` configuration field

2. **`src/hub/dependencies.py`** - Added `get_embedding_service_client` DI provider

3. **`src/hub/services/llm_client.py`** - Added `chat_helper()` method
   - 60-second timeout (shorter than full chat models)
   - Supports both completion-style (`prompt` field) and chat-style (`messages` field) APIs
   - Explicit failure handling with structured responses
   - Retries once on timeout before failing

4. **`src/hub/tools/__init__.py`** - Registered `chat_embeddings` tool
   - Uses LLM_REQUIREMENT policy
   - Parameters: service_id/service_name, text/texts, encoding_format
   - Properly structured JSON Schema with combined oneOf constraints

5. **`src/hub/lifespan.py`** - Added embedding client initialization to app state

## Acceptance Criteria Verification

| Criterion | Status | Implementation |
|-----------|--------|----------------|
| Helper-model alias routing defined | ✅ | `chat_helper()` method in LLMServiceClient with 60s timeout, supports both completion and chat-style APIs |
| Embedding-service adapter contract explicit | ✅ | `EmbeddingServiceClient` class with `embed()` and `embed_batch()` methods, 30s timeout, structured responses |
| Timeout and failure behavior planned | ✅ | Per-service timeouts (60s helper, 30s embedding) with structured error responses including latency_ms |

## Validation

- All ruff checks pass
- Type hints complete for all new functions and methods
- Docstrings present following project conventions
- Structured logging with service_id, latency_ms, and error details

## Integration Points

- Embedding client initialized in lifespan and stored in app.state
- DI provider follows existing pattern for LLMServiceClient
- Tool registration uses existing LLM_REQUIREMENT policy
- Service type validation ensures only EMBEDDING-type services are used

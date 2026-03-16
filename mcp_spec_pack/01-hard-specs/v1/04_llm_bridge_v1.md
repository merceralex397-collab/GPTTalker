# V1 Hard Spec — LLM Bridge

## Simple explanation

This is the part that lets ChatGPT ask other AI systems for help.

In plain terms:
- ChatGPT remains the main planner
- the MCP hub can ask a separate local model or coding agent to do focused work
- this is useful when the other model has repo access, different strengths, or lower cost

## Status

Hard-set specification.

## Goals

Provide controlled access to approved LLM and coding-agent backends.

## Requirements

- V1 SHALL support named LLM service aliases.
- V1 SHALL support a main LLM backend on a separate machine.
- V1 SHALL support optional small helper models for narrow tasks.
- V1 SHALL route by service alias, not arbitrary URL.
- Responses SHALL include backend name and timing metadata.
- Streaming MAY be deferred if it complicates V1.

## Architecture

Backend classes:
1. coding-agent backend
   - e.g. OpenCode server
2. general text backend
   - local inference server
3. helper model backend
   - small model for classification, summarization, or context compression
4. embedding backend
   - model/service used to create vectors for project context

## Interfaces and behavior

Primary tool:

### `chat_llm(node, service, prompt, context=None, session_id=None)`

Required behavior:
- validate service alias
- route to approved backend
- preserve session if backend supports sessions
- return structured response

Recommended service metadata:
- `kind`: `coding_agent | general_llm | helper_llm | embedding_service`
- `supports_sessions`
- `supports_streaming`
- `max_context_class`
- `intended_use`

Special OpenCode support:
- V1 SHOULD support a dedicated OpenCode adapter.
- Session-aware methods MAY include:
  - `opencode_new_session`
  - `opencode_prompt`
  - `opencode_status`

## Failure modes

- Backend offline: return service-unavailable.
- Timeout: return timeout plus backend metadata.
- Unsupported operation: return explicit capability error.
- Session missing/expired: return session-not-found.
- Malformed backend response: return adapter-error.

## Security considerations

- Backends SHALL be allowlisted.
- Credentials for remote providers SHALL not be stored in generated docs.
- Prompt and response logging SHOULD be configurable because logs may contain sensitive code or text.
- For coding-agent backends, V1 SHALL prefer read-oriented workflows.

## Implementation notes

Strong recommendation for your setup:
- main coding/analysis model on the stronger 32GB machine
- optional small helper model on the hub or another light machine
- embedding model separated from the main reasoning model when practical

This reduces load on the main model and keeps the hub responsive.

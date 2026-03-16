# V2 Hard Spec — Distributed LLM Execution

## Simple explanation

This is the part that spreads AI work across multiple machines.

In plain terms:
- not every job should hit the same model or same box
- small jobs can go to a small model
- heavy jobs can go to the best machine
- embedding work can go to a specialist service

## Status

Hard-set specification.

## Goals

Support multi-machine, multi-model AI routing.

## Requirements

- V2 SHALL support at least:
  - one main LLM node
  - optional helper LLM node/service
  - optional embedding service
- V2 SHALL classify tasks into routing classes.
- V2 SHALL track backend health and availability.
- V2 SHALL support fallback backends where configured.

## Architecture

Routing classes:
- quick classification
- summarization/compression
- embeddings
- code analysis
- long-form reasoning
- coding-agent delegation

## Interfaces and behavior

Required controls:
- model registry
- backend capability metadata
- scheduler policies
- health checks
- load and queue metadata

Required tool:
- `route_task(task_type, preferred_repo=None, size_hint=None)`

## Failure modes

- Chosen model unavailable: fallback policy.
- Queue overload: reject or delay with clear reason.
- Capability mismatch: reject and reroute if possible.

## Security considerations

More models means more secrets, more logs, and more surfaces to secure. Keep per-service auth and narrow network exposure.

## Implementation notes

For your setup, this lets the old laptop remain a control plane while the stronger 32GB box does the heavy lifting.

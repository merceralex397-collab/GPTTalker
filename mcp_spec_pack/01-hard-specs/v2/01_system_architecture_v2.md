# V2 Hard Spec — System Architecture

## Simple explanation

V2 is the more advanced system. It still keeps safety boundaries, but it adds stronger project intelligence, cross-repo reasoning, and distributed model routing.

In plain terms:
- V1 is the safe working skeleton
- V2 is the grown-up system with richer memory and smarter routing

## Status

Hard-set specification.

## Goals

Expand the system beyond narrow tool execution into richer project intelligence.

## Requirements

- V2 SHALL preserve all V1 constraints unless explicitly expanded.
- V2 SHALL support cross-repo context retrieval.
- V2 SHALL support distributed LLM routing and scheduling.
- V2 SHALL support issue intelligence and historical analysis.
- V2 SHALL support automatic project summaries and architecture maps.

## Architecture

New V2 layers:
- scheduler/router
- multi-repo retrieval
- issue intelligence layer
- architecture graph
- optional local automation loops

## Interfaces and behavior

New core capabilities:
- global search across repos
- dependency and relationship mapping
- richer issue and failure tracking
- model routing by task class and machine capacity
- generated context bundles tailored per request

## Failure modes

- Scheduler unavailable: fallback to static default backend.
- Global context unavailable: fallback to per-repo context.
- Graph build failure: preserve prior graph snapshot.

## Security considerations

V2 increases system sensitivity because it centralizes more knowledge. Access controls and deletion policies become more important.

## Implementation notes

V2 should be added only after V1 is stable and trusted in day-to-day use.

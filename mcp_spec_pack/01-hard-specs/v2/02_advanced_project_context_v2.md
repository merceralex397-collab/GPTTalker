# V2 Hard Spec — Advanced Project Context

## Simple explanation

This version makes project context feel more like a living project memory.

In plain terms:
- it tracks not just docs and file summaries
- but also recurring issues, architecture relationships, and important changes over time

## Status

Hard-set specification.

## Goals

Add richer, more complete project memory.

## Requirements

- V2 SHALL support hybrid retrieval:
  - keyword
  - semantic
  - graph-assisted
- V2 SHALL maintain issue histories.
- V2 SHALL maintain architecture summaries and module maps.
- V2 SHALL support context bundle generation tailored to a question or task.

## Architecture

V2 context layers:
1. vector search
2. structured issue/history store
3. graph of modules/services/ownership/dependencies
4. generated summaries

## Interfaces and behavior

Required additions:
- `build_context_bundle(node, repo, task_type, query)`
- `list_recurring_issues(node, repo)`
- `get_architecture_map(node, repo)`
- `search_global_context(query)`

## Failure modes

- Stale graph data: mark timestamp and confidence.
- Contradictory issue records: preserve provenance and show both.
- Oversized context bundle: return prioritized subset.

## Security considerations

Need stronger redaction and access policy because context becomes more comprehensive and potentially more revealing.

## Implementation notes

This is where the system starts to feel genuinely useful as a project brain rather than just a repo file reader.

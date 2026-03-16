# V2 Hard Spec — Observability, History, and Memory

## Simple explanation

This is the trace and audit layer.

In plain terms:
- the system remembers what it did
- what files were generated
- what issues were found
- which model was used
- what changed over time

## Status

Hard-set specification.

## Goals

Provide durable history, auditing, and operational visibility.

## Requirements

- The system SHALL persist task history.
- The system SHALL persist generated document history.
- The system SHALL support issue timelines.
- The system SHALL support operator-readable logs and summaries.

## Architecture

History objects:
- tasks
- writes
- indexing runs
- issue updates
- model routing events
- backend failures

## Interfaces and behavior

Suggested tools:
- `list_task_history(filters=None)`
- `get_task_details(task_id)`
- `list_generated_docs(repo=None)`
- `get_issue_timeline(repo)`

## Failure modes

- Store unavailable: degrade to local log file.
- Log volume too large: rotate and archive.

## Security considerations

Logs may contain sensitive project data. Retention and redaction policies matter.

## Implementation notes

This layer is what makes the system trustworthy when you need to review what happened later.

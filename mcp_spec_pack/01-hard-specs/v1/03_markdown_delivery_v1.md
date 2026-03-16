# V1 Hard Spec — Markdown Delivery

## Simple explanation

This is the part that lets ChatGPT create useful documents without being allowed to write anywhere it wants.

In plain terms:
- ChatGPT writes markdown only
- only into approved folders
- with controlled filenames and paths
- for plans, specs, summaries, and notes

## Status

Hard-set specification.

## Goals

Enable safe document creation into approved project locations.

## Requirements

- Writes SHALL be limited to markdown or text-based documentation files.
- Writes SHALL be scoped to named write targets.
- The hub SHALL reject absolute paths and path traversal.
- Every write SHALL record:
  - node
  - repo/write target
  - relative path
  - content hash
  - timestamp
- V1 SHALL support create and overwrite modes.
- V1 SHOULD support optional no-overwrite mode.

## Architecture

Write target model:
- each node defines named write roots
- each write root maps to one filesystem directory
- writes are resolved as:
  `node + write_target + relative_path`

Examples:
- repo docs folder
- project plans folder
- architecture folder
- issue summaries folder

## Interfaces and behavior

Primary tool:

### `write_markdown(node, write_target, relative_path, content, mode="create_or_overwrite")`

Behavior:
1. validate node
2. validate write target
3. normalize relative path
4. verify extension policy
5. write file atomically
6. log write
7. optionally trigger context re-index of that doc

Recommended metadata returned:
- final path
- bytes written
- content hash
- created/updated flag

## Failure modes

- Unknown write target: fail closed.
- Invalid extension: reject.
- Existing file with no-overwrite mode: reject cleanly.
- Disk full / permission issue: fail and log.
- Partial write risk: use temporary file + atomic replace when possible.

## Security considerations

- No arbitrary filesystem writes.
- No shell redirects as a write mechanism.
- Enforce file extension allowlist.
- Strongly consider size limits to avoid abuse.
- Generated markdown should not automatically expose secrets found elsewhere in the system.

## Implementation notes

Recommended V1 write policy:
- `.md` required by default
- optional `.txt`
- per-target naming conventions
- include generated-by metadata block if desired

Useful examples:
- `/docs/plans/mcp-hub-brief.md`
- `/docs/specs/repo-context-v1.md`
- `/notes/issues/current-known-issues.md`

---
name: context-intelligence
description: Hold GPTTalker’s Qdrant, indexing, issue-memory, and cross-repo intelligence conventions.
---

# Context Intelligence

Use this skill for semantic indexing, retrieval, and context-bundle work.

## Rules

- keep vector-store access behind shared modules rather than scattered clients
- persist provenance metadata for every retrieved or indexed context fragment
- keep indexing idempotent through content hashes and tracked file state
- respect repo access controls in cross-repo search and architecture outputs
- treat embedding-model details as implementation choices unless the ticket explicitly locks them down

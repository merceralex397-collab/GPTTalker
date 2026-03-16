---
name: process-doctor
description: Re-run repo-process-doctor safely after scaffold or workflow changes and record what was replaced versus preserved.
---

# Process Doctor

Use this skill when the generated operating layer changes materially.

## Checklist

1. inspect `.opencode/meta/bootstrap-provenance.json`
2. inspect `.opencode/state/workflow-state.json`
3. run the repo-process-doctor audit
4. record whether managed-surface replacement occurred
5. note which surfaces were intentionally preserved and why

## GPTTalker note

For this repo, `mcp_spec_pack/` is the preserved immutable reference source. Generated surfaces may be replaced aggressively as long as that source pack remains untouched.

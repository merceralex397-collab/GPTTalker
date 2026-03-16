# Proposal — Indexing Trigger Options

## Simple explanation

This is about when the system updates project context.

In plain terms:
- if the repo changes, how does the project memory stay fresh?

## Status

Proposal document.

## Options

### Option A — Manual indexing
You tell the system when to refresh.

Advantages:
- simplest
- predictable
- no background surprise work

Downsides:
- easy to forget
- context may go stale

Best use:
- early version or low-change repos

### Option B — Git-hook-driven indexing
Index refresh runs after commits or other git events.

Advantages:
- context stays close to code changes
- automatic for normal development flows

Downsides:
- more setup
- may miss non-git events
- can feel intrusive if hooks slow things down

Best use:
- repos with regular disciplined commit flow

### Option C — Scheduled indexing
The system refreshes on a time schedule.

Advantages:
- simple automation
- no need to remember
- catches drift over time

Downsides:
- may do unnecessary work
- may still lag behind immediate changes

Best use:
- mixed human habits across many machines

### Option D — Event hybrid
Manual + write-trigger + scheduled fallback.

Advantages:
- strongest overall behavior
- generated docs are re-indexed fast
- scheduled refresh catches missed changes

Downsides:
- more complexity

## Recommendation

Recommended proposal: start with manual plus write-triggered refresh for generated markdown, then add scheduled fallback later.

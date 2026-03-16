# Proposal — Scheduler and Routing Layer

## Simple explanation

A scheduler decides which backend should handle a task.

In plain terms:
- not every question should hit the same model
- the scheduler picks the most suitable worker

## Status

Proposal document.

## Options

### Why this is useful
Without a scheduler:
- heavy model gets overloaded
- small jobs waste expensive compute
- embeddings and helper work interfere with analysis jobs

### What it can do
- choose model by task type
- check machine health
- pick fallback if a service is down
- prefer local/context-rich backends for repo work
- send tiny jobs to tiny models

### Advantages
- better performance
- better use of weak hardware
- cleaner user experience

### Downsides
- more design work
- bad routing rules can hurt quality

### Suggested task classes
- route: helper-model
- embed: embedding service
- summarize: helper or main depending on size
- code analysis: main model or OpenCode
- deep planning: main model

### Operational rule
The scheduler should be policy-driven, not magical.
That means:
- explicit backend capabilities
- explicit fallback order
- no hidden guessing where possible

## Recommendation

Recommended in V2. Optional as a simple static policy table in late V1.

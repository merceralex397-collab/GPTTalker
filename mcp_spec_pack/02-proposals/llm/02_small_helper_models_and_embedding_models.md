# Proposal — Small Helper Models and Embedding Models

## Simple explanation

A small helper model is a second, lighter AI used for narrow jobs so the main model does not have to do everything.

In plain terms:
- main model = expensive brain
- helper model = cheap assistant for smaller tasks
- embedding model = creates vectors for meaning-based search

## Status

Proposal document.

## Options

### Proposal A — Small helper model
Possible jobs:
- classify request type
- choose backend
- summarize long logs before sending onward
- compress context
- label issue severity
- generate tags

Potential examples:
- Phi-class small models
- other lightweight instruction models

Advantages:
- saves load on main model
- faster for small decisions
- useful on weaker hardware

Downsides:
- more moving parts
- helper quality can be limited

### Proposal B — Dedicated embedding model/service
Possible jobs:
- convert docs and summaries into vectors
- power semantic project search

Advantages:
- keeps embedding work away from the main model
- often cheaper and simpler
- more predictable indexing pipeline

Downsides:
- another service to manage

### Proposal C — Combined helper + embedding setup
One small model/service family handles lightweight semantic tasks while the main model focuses on analysis.

Advantages:
- clean separation of labor
- helps your 32GB CPU-only main machine avoid unnecessary work

Downsides:
- more architecture complexity

## Recommendation

Recommended proposal: yes, add a small helper model and a dedicated embedding model/service. This is especially helpful on constrained hardware.

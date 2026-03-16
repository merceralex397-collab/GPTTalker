# Proposal — Knowledge Graph and Context Bundle Designs

## Simple explanation

A knowledge graph is a structured map of how project pieces relate. A context bundle is a ready-made packet of the most relevant project information for a task.

In plain terms:
- vector DB helps find similar meaning
- graph helps explain relationships
- context bundle gives the model a compact brief instead of a messy dump

## Status

Proposal document.

## Options

### Proposal A — Knowledge graph
Tracks things like:
- modules
- services
- dependencies
- ownership
- key files
- issue links

Advantages:
- better structural reasoning
- easier architecture understanding
- useful for cross-repo analysis

Downsides:
- more work to build and keep fresh

### Proposal B — Context bundles
For a given task, the system prepares:
- repo summary
- important files
- relevant docs
- related issues
- recent changes

Advantages:
- very practical
- reduces token waste
- improves consistency

Downsides:
- bundle quality depends on retrieval quality

### Proposal C — Combined model
Use graph + vector retrieval + bundle assembly.

Advantages:
- strongest long-term design
- best project understanding

Downsides:
- more engineering effort

## Recommendation

Recommended proposal: context bundles early; knowledge graph once the core context system is stable.

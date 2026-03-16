# Proposal — Context Source Options

## Simple explanation

This is about what should be stored as project knowledge.

In plain terms:
- what information should the system remember about each repo?

## Status

Proposal document.

## Options

Potential sources:

### Source group 1 — Docs and markdown
Includes:
- README
- docs
- plans
- specs
- issue notes

Why useful:
- usually the highest signal and easiest to search

### Source group 2 — Code summaries
Instead of storing every line of code directly, store summaries of important files/modules.

Why useful:
- lower storage cost
- better high-level context

### Source group 3 — Commit messages
Why useful:
- helps understand recent changes and intent

Downsides:
- commit messages can be noisy or low quality

### Source group 4 — Error logs / issue logs
Why useful:
- recurring failures are often the most valuable operational memory

### Source group 5 — Generated architecture summaries
Why useful:
- gives ChatGPT a compact explanation of the project

### Source group 6 — Chat/task history
Why useful:
- remembers what was already investigated or planned

Downsides:
- can become noisy if not curated

## Recommendation

Recommended proposal: include all of them, but treat docs, issue notes, architecture summaries, and selected code summaries as the highest-value tier.

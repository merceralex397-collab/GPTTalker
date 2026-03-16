# Proposal — Vector Database Options

## Simple explanation

A vector database is a way to store the “meaning” of text so the system can find relevant project information even when the wording is different.

In plain terms:
- normal search finds exact words
- vector search finds similar meaning
- this is useful when the system needs project context quickly

## Status

Proposal document.

## Options

### Option A — Per-repo vector index
Each repo has its own separate meaning-search database.

Advantages:
- clean isolation
- simpler permissions
- easier deletion per repo
- good performance for repo-local queries

Downsides:
- more separate indexes to manage
- harder to search across many repos

Best use:
- mostly single-repo work

### Option B — Global vector index
All repos go into one large semantic index with metadata tags.

Advantages:
- easier cross-repo search
- simpler single search endpoint

Downsides:
- weaker isolation
- can get noisy
- careful metadata filtering becomes essential

Best use:
- many related repos with shared concepts

### Option C — Hybrid model
Per-repo indexes plus a smaller global index for summaries/issues/docs.

Advantages:
- best balance
- repo-local precision plus cross-repo awareness
- easier to keep global index smaller and cleaner

Downsides:
- most design complexity
- two retrieval layers to maintain

### Candidate technologies

#### Qdrant
What it is:
- a vector database with strong filtering support

Why it is good:
- good metadata filtering
- serious enough for scale
- a good fit if you want durable project search

Tradeoffs:
- more “database-like” than the lightest options

#### LanceDB
What it is:
- local analytical/vector storage focused on efficient local workflows

Why it is good:
- attractive for local-first setups
- good performance characteristics

Tradeoffs:
- smaller ecosystem than some larger options

#### Chroma
What it is:
- simple local vector DB used widely in prototypes

Why it is good:
- easy to start with

Tradeoffs:
- often feels more prototype-oriented than long-term operational backbone

#### SQLite + embeddings manually
What it is:
- a homemade lightweight approach

Why it is good:
- very small footprint
- very understandable

Tradeoffs:
- you have to build more yourself

## Recommendation

Recommended proposal: hybrid index model, backed by Qdrant if you want robustness or LanceDB if you want local-first simplicity.

---
name: context-intelligence
description: Qdrant integration and context intelligence patterns for GPTTalker. Use when implementing, modifying, or debugging the embedding pipeline, vector search, context bundle assembly, or cross-repo intelligence features.
---

# Context Intelligence — GPTTalker

## Overview

GPTTalker uses Qdrant as its vector store to enable semantic search across all indexed repos. The context intelligence pipeline takes source code and documentation, chunks it, generates embeddings, stores them in Qdrant, and retrieves relevant context when ChatGPT needs it.

All context intelligence code lives in `src/hub/context/`.

## Qdrant Integration Patterns

### Client Setup

Use the async Qdrant client for all operations:

```python
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

client = AsyncQdrantClient(host="localhost", port=6333)
```

### Collection Strategy

GPTTalker uses a **per-repo + global** collection strategy:

| Collection | Naming | Contents |
|---|---|---|
| Per-repo | `repo_{repo_name}` | All chunks from a single repo |
| Global | `global_cross_repo` | Selected high-value chunks from all repos |

**Per-repo collections** enable fast, scoped searches within a single repo.

**The global collection** enables cross-repo semantic search — finding related code, patterns, or docs across the entire dev environment.

### Collection Creation

```python
await client.create_collection(
    collection_name=f"repo_{repo_name}",
    vectors_config=VectorParams(
        size=EMBEDDING_DIM,  # Match your embedding model's output dimension
        distance=Distance.COSINE,
    ),
)
```

## Embedding Pipeline

### Pipeline Stages

```
Source files → Chunking → Embedding → Qdrant upsert
```

### 1. Text Chunking

Split source files into meaningful chunks:

```python
class Chunk(BaseModel):
    repo_name: str
    file_path: str
    chunk_index: int
    content: str
    start_line: int
    end_line: int
    language: str | None = None
```

**Chunking rules:**
- Chunk by logical boundaries (functions, classes, markdown sections) when possible
- Fall back to sliding window with overlap for unstructured text
- Target chunk size: 500–1500 tokens (adjust based on embedding model limits)
- Always preserve enough context for the chunk to be understandable in isolation
- Include file path and line numbers in chunk metadata

### 2. Embedding Generation

```python
async def embed_chunks(chunks: list[Chunk]) -> list[list[float]]:
    """Generate embeddings for a batch of chunks."""
    texts = [chunk.content for chunk in chunks]
    # Use your embedding model (e.g., sentence-transformers, OpenAI embeddings)
    embeddings = await embedding_model.encode(texts)
    return embeddings
```

**Rules:**
- Batch embedding requests for efficiency
- Cache embeddings keyed by content hash to avoid re-embedding unchanged files
- Use the same embedding model for indexing and querying

### 3. Qdrant Upsert

```python
await client.upsert(
    collection_name=f"repo_{repo_name}",
    points=[
        PointStruct(
            id=generate_point_id(chunk),
            vector=embedding,
            payload={
                "repo_name": chunk.repo_name,
                "file_path": chunk.file_path,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "language": chunk.language,
            },
        )
        for chunk, embedding in zip(chunks, embeddings)
    ],
)
```

**Always include these payload fields:** `repo_name`, `file_path`, `chunk_index`, `content`, `start_line`, `end_line`.

## Hybrid Retrieval (Keyword + Semantic)

For best results, combine keyword search with semantic search:

### Semantic Search (Qdrant)

```python
results = await client.search(
    collection_name=collection_name,
    query_vector=query_embedding,
    limit=top_k,
    score_threshold=0.7,  # Adjust based on quality needs
)
```

### Keyword Search (SQLite or Qdrant payload filter)

```python
# Using Qdrant payload filter for keyword matching
from qdrant_client.models import Filter, FieldCondition, MatchText

results = await client.search(
    collection_name=collection_name,
    query_vector=query_embedding,
    query_filter=Filter(
        must=[
            FieldCondition(key="content", match=MatchText(text=keyword))
        ]
    ),
    limit=top_k,
)
```

### Hybrid Merge Strategy

1. Run semantic search → get top N results with similarity scores
2. Run keyword search → get top M results
3. Merge and deduplicate by `(repo_name, file_path, chunk_index)`
4. Re-rank by a weighted combination of semantic score and keyword match relevance
5. Return top K final results

## Context Bundle Assembly

When ChatGPT requests project context, assemble a **context bundle** — a structured package of relevant information:

```python
class ContextBundle(BaseModel):
    query: str
    repo_scope: str | list[str]  # "all" or specific repo names
    results: list[ContextResult]
    total_chunks_searched: int
    retrieval_method: str  # "semantic", "keyword", "hybrid"

class ContextResult(BaseModel):
    repo_name: str
    file_path: str
    content: str
    relevance_score: float
    start_line: int
    end_line: int
    language: str | None = None
```

### Bundle Assembly Rules

- Respect token budgets — estimate total tokens and truncate if needed
- Order results by relevance score (highest first)
- Include file path context so ChatGPT can reference specific locations
- Deduplicate overlapping chunks from the same file
- Include metadata about the search (method, scope, total results) for transparency

## Cross-Repo Search Patterns

Cross-repo search queries the **global collection** or iterates across per-repo collections:

### Strategy 1: Global Collection (Preferred)

```python
# Search the global cross-repo collection
results = await client.search(
    collection_name="global_cross_repo",
    query_vector=query_embedding,
    limit=top_k,
)
# Results already include repo_name in payload for attribution
```

### Strategy 2: Fan-Out Search

```python
# Search each per-repo collection and merge results
all_results = []
for repo_name in registered_repos:
    results = await client.search(
        collection_name=f"repo_{repo_name}",
        query_vector=query_embedding,
        limit=per_repo_limit,
    )
    all_results.extend(results)

# Sort by score and take top K
all_results.sort(key=lambda r: r.score, reverse=True)
final_results = all_results[:top_k]
```

### When to Use Each

- **Global collection**: Fast, single query, best for broad "find anything related" searches
- **Fan-out**: Better when you need guaranteed coverage of every repo, or when repos have very different content scales

## Indexing Lifecycle

### When to Re-Index

- On initial repo registration (full index)
- On git push / file change events (incremental index)
- On manual trigger (re-index command)

### Incremental Indexing

- Track indexed file hashes in SQLite
- On re-index, compare current file hashes to stored hashes
- Only re-embed changed or new files
- Delete vectors for removed files

```python
class IndexedFile(BaseModel):
    repo_name: str
    file_path: str
    content_hash: str
    last_indexed: datetime
    chunk_count: int
```

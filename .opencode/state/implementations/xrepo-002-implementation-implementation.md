# Implementation Summary: XREPO-002 — Repo Relationships and Landscape Metadata

## Overview

This implementation adds explicit relationship metadata tracking and structured landscape ownership for the cross-repo intelligence layer.

## New Files Created

| File | Purpose |
|------|---------|
| `src/shared/repositories/relationships.py` | SQLite repositories for relationships and repo owners |
| `src/hub/services/relationship_service.py` | Service for managing repo relationships with CRUD operations |
| `src/hub/tools/relationships.py` | MCP tool handlers for relationship management |

## Files Modified

| File | Modification |
|------|-------------|
| `src/shared/models.py` | Added `RelationshipType`, `RepoOwner`, `RepoRelationship`, `LandscapeSource`, `LandscapeMetadata` models; Extended `RepoMetadata` with `owner` field; Extended `ProjectLandscape` with `landscape_metadata` field |
| `src/shared/tables.py` | Added `CREATE_RELATIONSHIPS_TABLE`, `CREATE_REPO_OWNERS_TABLE`, updated `SCHEMA_VERSION` to 3, added relationship indexes |
| `src/shared/migrations.py` | Added migration 3 for relationships and repo_owners tables |
| `src/shared/repositories/__init__.py` | Exported `RelationshipRepository` and `RepoOwnerRepository` |
| `src/hub/services/cross_repo_service.py` | Extended to include owner metadata and source citations in landscape views |
| `src/hub/dependencies.py` | Added DI providers for relationship and owner repositories, and relationship service |
| `src/hub/tools/__init__.py` | Added `register_relationship_tools()` and integrated with `register_all_tools()` |

## Acceptance Criteria Verification

### 1. Relationship Metadata Model Explicit
- ✅ `RelationshipType` enum defines valid relationship types (depends_on, related_to, forks_from, contains, references, shared_dep)
- ✅ `RepoRelationship` model includes all required fields: relationship_id, source_repo_id, target_repo_id, relationship_type, description, confidence, bidirectional, created_at, created_by, source_record, metadata
- ✅ `RelationshipRepository` provides full CRUD operations

### 2. Landscape Metadata Structured Owner
- ✅ `RepoOwner` model includes owner_id, name, email, role, added_at, metadata
- ✅ `LandscapeMetadata` includes owner, maintainers, sources, relationship_count, description, tags, category
- ✅ `RepoMetadata` extended with optional owner field
- ✅ `get_project_landscape` now returns owner metadata for each repo

### 3. Cross-Repo Views Cite Source Records
- ✅ `LandscapeSource` model tracks source_type, source_id, repo_id, node_id, citation, included_at
- ✅ `get_project_landscape` returns `landscape_metadata` with sources array
- ✅ Each repo and relationship in landscape views includes source citation

## New MCP Tools

| Tool | Description |
|------|-------------|
| `create_relationship` | Create explicit repo relationship with provenance |
| `list_relationships` | List relationships filtered by repo or type |
| `delete_relationship` | Delete a relationship |
| `set_repo_owner` | Set owner information for a repository |
| `get_repo_owner` | Get owner information for a repository |

## Database Schema

```sql
-- Relationships table
CREATE TABLE relationships (
    relationship_id TEXT PRIMARY KEY,
    source_repo_id TEXT NOT NULL,
    target_repo_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    description TEXT,
    confidence REAL DEFAULT 1.0,
    bidirectional INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL,
    source_record TEXT,
    metadata TEXT DEFAULT '{}',
    FOREIGN KEY (source_repo_id) REFERENCES repos(repo_id) ON DELETE CASCADE,
    FOREIGN KEY (target_repo_id) REFERENCES repos(repo_id) ON DELETE CASCADE
);

-- Repo owners table
CREATE TABLE repo_owners (
    repo_id TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL,
    name TEXT NOT NULL,
    email TEXT,
    role TEXT DEFAULT 'maintainer',
    added_at TEXT NOT NULL,
    metadata TEXT DEFAULT '{}',
    FOREIGN KEY (repo_id) REFERENCES repos(repo_id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_relationships_source ON relationships(source_repo_id);
CREATE INDEX idx_relationships_target ON relationships(target_repo_id);
CREATE INDEX idx_relationships_type ON relationships(relationship_type);
```

## Integration Points

- **CORE-002 (Repo Registry)**: Validates repo IDs exist when creating relationships
- **CTX-001 (Qdrant)**: Uses existing collections for context retrieval
- **XREPO-001 (Cross-repo search)**: Extended landscape views to cite source records
- **SETUP-003 (SQLite)**: New relationships and repo_owners tables via migration v3

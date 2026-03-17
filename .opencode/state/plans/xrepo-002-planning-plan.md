# Implementation Plan: XREPO-002 — Repo Relationships and Landscape Metadata

## 1. Scope

This ticket implements explicit relationship metadata tracking and structured landscape ownership for the cross-repo intelligence layer. It builds on the existing cross-repo search (XREPO-001), Qdrant integration (CTX-001), and repo registry (CORE-002) to add:

- **Explicit relationship metadata model** — Relationships are no longer computed ad-hoc but stored persistently with provenance
- **Structured landscape ownership** — Repos and landscapes include owner/maintainer metadata
- **Citable source records** — All cross-repo views include explicit citations to their source records

## 2. Files and Systems Affected

### New Files to Create

| File | Purpose |
|------|---------|
| `src/shared/models.py` (extension) | Add `RepoRelationship`, `RelationshipType`, `RepoOwner`, `LandscapeSource` models |
| `src/hub/services/relationship_service.py` | Service for managing repo relationships with CRUD operations |
| `src/hub/tools/relationships.py` | MCP tool handlers for relationship management |
| `src/shared/repositories/relationships.py` | SQLite repository for relationship persistence |

### Files to Modify

| File | Modification |
|------|-------------|
| `src/shared/models.py` | Add new relationship and owner models |
| `src/hub/services/cross_repo_service.py` | Update to use explicit relationships in landscape views |
| `src/hub/tools/cross_repo.py` | Add citation/source tracking to existing tools |
| `src/shared/repositories/__init__.py` | Export new RelationshipRepository |
| `src/hub/dependencies.py` | Add DI providers for relationship service |
| `src/shared/models.py` (existing) | Extend `RepoMetadata` with owner field |

### Systems Affected

- **SQLite**: New `relationships` table for storing explicit repo relationships
- **Qdrant**: New collection `gpttalker_relationships` for relationship vector storage (optional, for semantic relationship search)
- **MCP Tools**: New tool `manage_relationship`, extended `get_project_landscape` with owner and citation data

## 3. Implementation Steps

### Step 1: Define Relationship and Owner Models

Add new models to `src/shared/models.py`:

```python
class RelationshipType(StrEnum):
    """Valid relationship types between repositories."""
    
    DEPENDS_ON = "depends_on"          # Repo A depends on Repo B
    RELATED_TO = "related_to"          # General relationship (shared code, similar domain)
    FORKS_FROM = "forks_from"          # Repo A is a fork of Repo B
    CONTAINS = "contains"              # Repo A contains Repo B as submodule
    REFERENCES = "references"         # Repo A references Repo B (imports, docs)
    SHARED_DEPENDENCY = "shared_dep"    # Both repos share a dependency


class RepoOwner(BaseModel):
    """Structured owner information for a repository."""
    
    owner_id: str = Field(..., description="Unique owner identifier")
    name: str = Field(..., description="Human-readable owner name")
    email: str | None = Field(None, description="Owner email")
    role: str = Field("maintainer", description="Owner role: maintainer, contributor, observer")
    added_at: datetime = Field(default_factory=datetime.utcnow, description="When owner was added")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional owner metadata")


class RepoRelationship(BaseModel):
    """Explicit relationship between two repositories."""
    
    relationship_id: str = Field(..., description="Unique relationship identifier")
    source_repo_id: str = Field(..., description="Source repository ID")
    target_repo_id: str = Field(..., description="Target repository ID")
    relationship_type: RelationshipType = Field(..., description="Type of relationship")
    
    # Relationship metadata
    description: str | None = Field(None, description="Human-readable relationship description")
    confidence: float = Field(1.0, description="Confidence score (0.0-1.0)", ge=0.0, le=1.0)
    bidirectional: bool = Field(False, description="Whether relationship applies both ways")
    
    # Provenance
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    created_by: str = Field(..., description="Who created this relationship (trace_id)")
    source_record: str | None = Field(
        None, description="Source record citation (e.g., 'git log', 'import scan', 'manual')"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class LandscapeSource(BaseModel):
    """Source citation for a landscape or cross-repo view."""
    
    source_type: str = Field(..., description="Type of source: repo, relationship, issue, file")
    source_id: str = Field(..., description="Unique identifier of the source")
    repo_id: str = Field(..., description="Repository the source belongs to")
    node_id: str = Field(..., description="Node hosting the repo")
    citation: str = Field(..., description="Human-readable citation text")
    included_at: datetime = Field(default_factory=datetime.utcnow, description="When included")


class LandscapeMetadata(BaseModel):
    """Extended landscape metadata with ownership and sources."""
    
    # Ownership
    owner: RepoOwner | None = Field(None, description="Primary owner of this landscape view")
    maintainers: list[RepoOwner] = Field(default_factory=list, description="All maintainers")
    
    # Provenance tracking
    sources: list[LandscapeSource] = Field(
        default_factory=list, description="Source records cited in this landscape"
    )
    relationship_count: int = Field(0, description="Number of explicit relationships included")
    
    # Extended metadata
    description: str | None = Field(None, description="Landscape description")
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    category: str | None = Field(None, description="Category (e.g., 'frontend', 'backend', 'infrastructure')")
```

### Step 2: Create Relationship Repository

Create `src/shared/repositories/relationships.py`:

```python
class RelationshipRepository:
    """SQLite repository for repo relationships."""
    
    async def create_relationship(self, relationship: RepoRelationship) -> bool:
        """Insert a new relationship."""
        
    async def get_relationship(self, relationship_id: str) -> RepoRelationship | None:
        """Get a relationship by ID."""
        
    async def list_by_repo(self, repo_id: str) -> list[RepoRelationship]:
        """List all relationships for a repo (as source or target)."""
        
    async def list_by_type(self, relationship_type: RelationshipType) -> list[RepoRelationship]:
        """List all relationships of a specific type."""
        
    async def update_relationship(self, relationship_id: str, **updates) -> bool:
        """Update relationship fields."""
        
    async def delete_relationship(self, relationship_id: str) -> bool:
        """Delete a relationship."""
        
    async def find_relationships(
        self,
        source_repo_id: str | None = None,
        target_repo_id: str | None = None,
        relationship_type: RelationshipType | None = None,
    ) -> list[RepoRelationship]:
        """Search relationships with filters."""
```

### Step 3: Create Relationship Service

Create `src/hub/services/relationship_service.py`:

```python
class RelationshipService:
    """Service for managing repo relationships."""
    
    async def create_relationship(
        self,
        source_repo_id: str,
        target_repo_id: str,
        relationship_type: RelationshipType,
        created_by: str,
        description: str | None = None,
        source_record: str | None = None,
    ) -> dict[str, Any]:
        """Create a new explicit relationship."""
        
    async def get_relationships_for_repo(
        self,
        repo_id: str,
        include_incoming: bool = True,
    ) -> list[RepoRelationship]:
        """Get all relationships for a repo."""
        
    async def get_landscape_with_ownership(
        self,
        include_relationships: bool = True,
    ) -> dict[str, Any]:
        """Get landscape with owner metadata and source citations."""
        
    async def add_owner_to_repo(
        self,
        repo_id: str,
        owner: RepoOwner,
    ) -> dict[str, Any]:
        """Add or update owner for a repo."""
```

### Step 4: Create MCP Tool Handlers

Create `src/hub/tools/relationships.py`:

```python
class CreateRelationshipParams(BaseModel):
    """Parameters for creating a repo relationship."""
    
    source_repo_id: str = Field(..., description="Source repository ID")
    target_repo_id: str = Field(..., description="Target repository ID")
    relationship_type: RelationshipType = Field(..., description="Type of relationship")
    description: str | None = Field(None, description="Relationship description")
    source_record: str | None = Field(None, description="Source of this relationship")


class SetRepoOwnerParams(BaseModel):
    """Parameters for setting repo owner."""
    
    repo_id: str = Field(..., description="Repository ID")
    owner_id: str = Field(..., description="Owner identifier")
    name: str = Field(..., description="Owner name")
    email: str | None = Field(None, description="Owner email")
    role: str = Field("maintainer", description="Owner role")


async def create_relationship_handler(...) -> dict[str, Any]:
    """Create an explicit repo relationship."""


async def list_relationships_handler(...) -> dict[str, Any]:
    """List relationships for a repo or all relationships."""


async def set_repo_owner_handler(...) -> dict[str, Any]:
    """Set owner information for a repository."""
```

### Step 5: Update Cross-Repo Service

Modify `src/hub/services/cross_repo_service.py`:

- Extend `get_project_landscape` to include owner metadata and source citations
- Use explicit relationships from the relationship service when `include_relationships=True`
- Add provenance tracking to all cross-repo views

### Step 6: Register New MCP Tools

Update `src/hub/tools/__init__.py` to register:
- `create_relationship` — Create explicit repo relationships
- `list_relationships` — List relationships for a repo
- `set_repo_owner` — Set owner for a repository

Extend existing tools:
- `get_project_landscape` — Now includes owner metadata and source citations
- `list_related_repos` — Uses explicit relationships when available

### Step 7: Update Dependencies

Add DI providers in `src/hub/dependencies.py`:
- `RelationshipRepository`
- `RelationshipService`

## 4. Validation Plan

### Acceptance Criteria Verification

| Criterion | Validation Method |
|-----------|-----------------|
| Relationship metadata model is explicit | Code inspection: New models (`RepoRelationship`, `RelationshipType`, `RepoOwner`) exist in `src/shared/models.py` with all required fields |
| Landscape metadata has a structured owner | Code inspection: `LandscapeMetadata` includes `owner` and `maintainers` fields; `get_project_landscape` returns owner data |
| Cross-repo views can cite their source records | Code inspection: `LandscapeSource` model exists; cross-repo tools include `sources` in responses |

### Unit Tests

- Test `RepoRelationship` model validation
- Test `RepoOwner` model validation  
- Test `RelationshipRepository` CRUD operations
- Test `RelationshipService.create_relationship` with access control
- Test `get_landscape_with_ownership` includes sources

### Integration Tests

- Test `create_relationship` MCP tool end-to-end
- Test `get_project_landscape` returns owner and source data
- Test relationship access control (cannot create relationship for inaccessible repos)

## 5. Risks and Assumptions

### Risks

1. **Relationship cardinality** — Without limits, users could create O(n²) relationships. **Mitigation**: Add reasonable limits (max 100 relationships per repo) and validation.

2. **Circular dependencies** — Bidirectional relationships could create cycles. **Mitigation**: Track direction explicitly; don't infer transitive relationships without explicit configuration.

### Assumptions

1. **Owner data is manual** — Unlike repos which are discovered/scanned, owners are expected to be added manually via MCP tools.

2. **Relationship sources are trusted** — The `source_record` field trusts the caller. This is acceptable since it's for provenance/citation, not access control.

3. **No automatic relationship inference** — This ticket focuses on explicit manual relationships. Automatic inference (e.g., from git history) can be a future enhancement.

## 6. Integration Points

| Dependency | Integration |
|-----------|------------|
| CORE-002 (Repo Registry) | Validate repo IDs exist when creating relationships |
| CTX-001 (Qdrant) | Use Qdrant for semantic relationship search (future enhancement) |
| XREPO-001 (Cross-repo search) | Extend landscape views to cite source records |
| SETUP-003 (SQLite) | New `relationships` table via migration |

## 7. Database Schema

```sql
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
    metadata TEXT,
    FOREIGN KEY (source_repo_id) REFERENCES repos(repo_id),
    FOREIGN KEY (target_repo_id) REFERENCES repos(repo_id)
);

CREATE INDEX idx_relationships_source ON relationships(source_repo_id);
CREATE INDEX idx_relationships_target ON relationships(target_repo_id);
CREATE INDEX idx_relationships_type ON relationships(relationship_type);

CREATE TABLE repo_owners (
    repo_id TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL,
    name TEXT NOT NULL,
    email TEXT,
    role TEXT DEFAULT 'maintainer',
    added_at TEXT NOT NULL,
    metadata TEXT,
    FOREIGN KEY (repo_id) REFERENCES repos(repo_id)
);
```

## 8. Implementation Summary

This ticket completes the cross-repo intelligence foundation by adding:

1. **Explicit relationship metadata** — No more ad-hoc overlap computation; relationships are stored persistently with provenance
2. **Structured ownership** — Repos and landscapes include owner/maintainer metadata for organizational clarity
3. **Citable cross-repo views** — All landscape outputs cite their sources, enabling auditability and traceability

The implementation follows the existing patterns in GPTTalker: Pydantic models for schemas, SQLite repositories for persistence, service classes for business logic, and MCP tool handlers for exposure.

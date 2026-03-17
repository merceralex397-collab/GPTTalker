# OBS-001 Planning: Task history, generated-doc log, and audit schema

## Scope

This ticket implements the observability foundation for GPTTalker by defining schemas and persistence for:
1. Task history (already partially exists via SETUP-003)
2. Generated document history with owner tracking
3. Audit records with trace metadata

These schemas power the observability tools defined in the canonical brief: `list_task_history`, `get_task_details`, `list_generated_docs`, and `get_issue_timeline`.

## Files and Systems Affected

### New Files to Create
- `src/shared/models.py` — Add `GeneratedDocRecord`, `AuditRecord`, and related models
- `src/shared/tables.py` — Add `generated_docs` and `audit_log` tables
- `src/shared/migrations.py` — Add migration v4 for new tables
- `src/shared/repositories/generated_docs.py` — New repository for generated document CRUD
- `src/shared/repositories/audit_log.py` — New repository for audit record CRUD

### Existing Files to Modify
- `src/shared/models.py` — Extend with new observability models
- `src/shared/tables.py` — Add new table definitions
- `src/shared/repositories/__init__.py` — Export new repositories
- `src/hub/dependencies.py` — Add DI providers for new repositories

## Implementation Steps

### Step 1: Define Models (src/shared/models.py)

Add the following new models:

```python
class DocOwner(BaseModel):
    """Owner information for generated documents."""
    owner_id: str = Field(..., description="Unique owner identifier")
    name: str = Field(..., description="Human-readable owner name")
    email: str | None = Field(None, description="Owner email")
    role: str = Field("generator", description="Role: generator, reviewer, approver")
    added_at: datetime = Field(default_factory=datetime.utcnow)


class GeneratedDocRecord(BaseModel):
    """Record of a generated/delivered document."""
    doc_id: UUID = Field(..., description="Unique document identifier")
    trace_id: str | None = Field(None, description="Trace ID for request tracking")
    tool_name: str = Field(..., description="Tool that generated this doc (e.g., write_markdown)")
    caller: str = Field(..., description="Caller identifier")
    target_path: str = Field(..., description="Path where document was written")
    content_hash: str = Field(..., description="SHA256 hash of document content")
    size_bytes: int = Field(..., description="Document size in bytes")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AuditEventType(StrEnum):
    """Valid audit event types."""
    TASK_EXECUTED = "task_executed"
    DOC_GENERATED = "doc_generated"
    POLICY_REJECTED = "policy_rejected"
    NODE_ACCESS = "node_access"
    REPO_ACCESS = "repo_access"
    LLM_REQUEST = "llm_request"
    INDEXING_RUN = "indexing_run"
    CONFIG_CHANGED = "config_changed"


class AuditRecord(BaseModel):
    """Audit log entry with full trace context."""
    audit_id: UUID = Field(..., description="Unique audit identifier")
    trace_id: str | None = Field(None, description="Trace ID linking to task")
    event_type: AuditEventType = Field(..., description="Type of audit event")
    actor: str = Field(..., description="Who triggered this event")
    target_type: str = Field(..., description="Target type: node, repo, doc, service")
    target_id: str | None = Field(None, description="Target identifier")
    action: str = Field(..., description="Action performed")
    outcome: str = Field(..., description="Outcome: success, failure, rejected")
    duration_ms: int | None = Field(None, description="Event duration")
    error: str | None = Field(None, description="Error message if failed")
    trace_context: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)
```

### Step 2: Define Table Schemas (src/shared/tables.py)

Add new table definitions:

```sql
CREATE_GENERATED_DOCS_TABLE = """
CREATE TABLE IF NOT EXISTS generated_docs (
    doc_id TEXT PRIMARY KEY,
    trace_id TEXT,
    tool_name TEXT NOT NULL,
    caller TEXT NOT NULL,
    target_path TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    metadata TEXT DEFAULT '{}'
);
"""

CREATE_AUDIT_LOG_TABLE = """
CREATE TABLE IF NOT EXISTS audit_log (
    audit_id TEXT PRIMARY KEY,
    trace_id TEXT,
    event_type TEXT NOT NULL,
    actor TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT,
    action TEXT NOT NULL,
    outcome TEXT NOT NULL,
    duration_ms INTEGER,
    error TEXT,
    trace_context TEXT DEFAULT '{}',
    metadata TEXT DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

# Add indexes
CREATE_AUDIT_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_audit_trace_id ON audit_log(trace_id);",
    "CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_log(event_type);",
    "CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_log(actor);",
    "CREATE INDEX IF NOT EXISTS idx_audit_created_at ON audit_log(created_at);",
    "CREATE INDEX IF NOT EXISTS idx_generated_docs_trace_id ON generated_docs(trace_id);",
    "CREATE INDEX IF NOT EXISTS idx_generated_docs_tool ON generated_docs(tool_name);",
]
```

### Step 3: Create Repositories

#### GeneratedDocsRepository (src/shared/repositories/generated_docs.py)

- `create(doc_id, tool_name, caller, target_path, content_hash, size_bytes, trace_id=None, metadata=None)` — Create new record
- `get(doc_id)` — Get by ID
- `list_all(limit=100)` — List recent docs
- `list_by_trace(trace_id)` — Get docs for a trace
- `list_by_tool(tool_name, limit=100)` — Filter by tool
- `list_by_caller(caller, limit=100)` — Filter by caller
- `delete(doc_id)` — Delete record
- `count_by_tool()` — Get counts per tool

#### AuditLogRepository (src/shared/repositories/audit_log.py)

- `create(event_type, actor, target_type, action, outcome, trace_id=None, target_id=None, duration_ms=None, error=None, trace_context=None, metadata=None)` — Create audit entry
- `get(audit_id)` — Get by ID
- `list_all(limit=100)` — List recent entries
- `list_by_trace(trace_id)` — Get entries for a trace
- `list_by_event_type(event_type, limit=100)` — Filter by type
- `list_by_actor(actor, limit=100)` — Filter by actor
- `list_by_target(target_type, target_id, limit=100)` — Filter by target
- `list_by_timerange(start, end, limit=100)` — Time-based filtering
- `delete(audit_id)` — Delete entry

### Step 4: Migration (src/shared/migrations.py)

Add migration v4:
- Create `generated_docs` table
- Create `audit_log` table
- Create indexes

### Step 5: DI Integration (src/hub/dependencies.py)

Add providers:
- `get_generated_docs_repository()` — Provide GeneratedDocsRepository
- `get_audit_log_repository()` — Provide AuditLogRepository

## Validation Plan

1. **Static Analysis**:
   - Run `ruff check src/shared/models.py src/shared/tables.py src/shared/repositories/generated_docs.py src/shared/repositories/audit_log.py`
   - Verify no import errors or type issues

2. **Schema Validation**:
   - Run migration against test database
   - Verify tables created with correct columns
   - Verify indexes created

3. **Repository Validation**:
   - Test CRUD operations for GeneratedDocsRepository
   - Test CRUD operations for AuditLogRepository
   - Verify query methods return correct data

4. **Integration Validation**:
   - Verify DI providers work in FastAPI context
   - Verify models serialize/deserialize correctly

## Risks and Assumptions

- **Assumption**: Task history table (from SETUP-003) is sufficient for core task tracking; this ticket extends with generated-doc and audit schemas
- **Risk**: Large audit log volume could impact performance — mitigated by proper indexing
- **Risk**: Trace context in audit records could contain sensitive data — mitigated by using existing redaction logic from logging.py

## Blockers

None. All dependencies resolved:
- SETUP-003 provides SQLite persistence and existing TaskRecord model
- SETUP-002 provides trace_id propagation and structured logging foundation

## Integration Points

- TaskRepository (existing) — Audit records link to task via trace_id
- write_markdown tool (WRITE-001) — Should call GeneratedDocsRepository on successful writes
- Policy engine (CORE-005) — Should emit audit events on rejections
- All MCP tools — Should integrate with AuditLogRepository for execution events

## Acceptance Criteria

1. **Task history schema defined** — TaskRecord model exists from SETUP-003; this ticket confirms schema adequacy and adds audit linking
2. **Generated-doc history has owner** — DocOwner model tracks who generated each document with role support
3. **Audit records include trace metadata** — AuditRecord includes trace_id, trace_context, actor, target_type, action, outcome for full traceability

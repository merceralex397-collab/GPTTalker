# OBS-001 Implementation: Task history, generated-doc log, and audit schema

## Summary

Implemented the observability foundation for GPTTalker by defining schemas and persistence for:
1. Task history (already exists via SETUP-003)
2. Generated document history with owner tracking
3. Audit records with trace metadata

## Changes Made

### New Files Created

1. **src/shared/repositories/generated_docs.py** - Repository for generated document CRUD operations
   - `create()` - Create new document record with content hash tracking
   - `get(doc_id)` - Get document by ID
   - `list_all(limit)` - List recent documents
   - `list_by_trace(trace_id)` - Get docs for a trace
   - `list_by_tool(tool_name, limit)` - Filter by tool
   - `list_by_caller(caller, limit)` - Filter by caller
   - `delete(doc_id)` - Delete record
   - `count_by_tool()` - Get counts per tool

2. **src/shared/repositories/audit_log.py** - Repository for audit record CRUD operations
   - `create()` - Create audit entry with full trace context
   - `get(audit_id)` - Get by ID
   - `list_all(limit)` - List recent entries
   - `list_by_trace(trace_id)` - Get entries for a trace
   - `list_by_event_type(event_type, limit)` - Filter by type
   - `list_by_actor(actor, limit)` - Filter by actor
   - `list_by_target(target_type, target_id, limit)` - Filter by target
   - `list_by_timerange(start, end, limit)` - Time-based filtering
   - `delete(audit_id)` - Delete entry
   - `count_by_event_type()` - Get counts per event type
   - `count_by_outcome()` - Get counts per outcome

### Modified Files

1. **src/shared/models.py** - Added new observability models:
   - `DocOwner` - Owner information for generated documents
   - `GeneratedDocRecord` - Record of a generated/delivered document
   - `AuditEventType` - Valid audit event types (StrEnum)
   - `AuditRecord` - Audit log entry with full trace context

2. **src/shared/tables.py** - Added new table definitions:
   - `CREATE_GENERATED_DOCS_TABLE` - Table for tracking generated documents
   - `CREATE_AUDIT_LOG_TABLE` - Table for audit trail with trace context
   - Added indexes for both tables (trace_id, event_type, actor, created_at, tool)
   - Updated SCHEMA_VERSION to 4

3. **src/shared/migrations.py** - Added migration v4:
   - Creates generated_docs table
   - Creates audit_log table
   - Creates all required indexes

4. **src/shared/repositories/__init__.py** - Added exports:
   - `GeneratedDocsRepository`
   - `AuditLogRepository`

5. **src/hub/dependencies.py** - Added DI providers:
   - `get_generated_docs_repository()` - Provide GeneratedDocsRepository
   - `get_audit_log_repository()` - Provide AuditLogRepository

## Acceptance Criteria Verification

1. **Task history schema defined** - TaskRecord model exists from SETUP-003; this implementation confirms schema adequacy and adds audit linking via trace_id

2. **Generated-doc history has owner** - DocOwner model tracks who generated each document with role support (generator, reviewer, approver). GeneratedDocRecord includes tool_name, caller, target_path, content_hash, size_bytes, and metadata.

3. **Audit records include trace metadata** - AuditRecord includes trace_id, trace_context (dict), actor, target_type, target_id, action, outcome, duration_ms, error for full traceability.

## Validation

- All files pass ruff lint checks (except pre-existing E402 for circular import workaround)
- Models properly inherit from Pydantic BaseModel
- Repository pattern follows existing codebase conventions
- DI providers integrate with FastAPI dependency injection
- Migration system properly extends version tracking

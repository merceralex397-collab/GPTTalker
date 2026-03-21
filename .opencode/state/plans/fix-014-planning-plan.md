# Implementation Plan for FIX-014: Replace placeholder tests with real implementations

## Scope

Replace placeholder tests in four test files with comprehensive test suites covering:
- `tests/hub/test_routing.py` - Tool registration and routing
- `tests/hub/test_transport.py` - MCP request/response handling  
- `tests/node_agent/test_executor.py` - Bounded subprocess execution and path validation
- `tests/shared/test_logging.py` - Trace-ID propagation and secret redaction

## Files or Systems Affected

### Test Files to Modify
1. `tests/hub/test_routing.py`
2. `tests/hub/test_transport.py`
3. `tests/node_agent/test_executor.py`
4. `tests/shared/test_logging.py`

### Source Files Under Test
1. `src/hub/tool_router.py` - ToolRegistry, ToolRouter, ToolDefinition
2. `src/hub/transport/mcp.py` - MCPTransport, parse_tool_call, format_tool_response
3. `src/hub/transport/base.py` - TransportError, TransportResult, TransportStatus
4. `src/node_agent/executor.py` - OperationExecutor with path validation
5. `src/shared/logging.py` - StructuredLogger, redact_sensitive, JSONFormatter
6. `src/shared/context.py` - trace_id_var, trace_context functions

## Implementation Steps

### 1. Replace test_routing.py with real tests

**Source module: `src/hub/tool_router.py`**

Remove placeholder tests and implement:

#### Happy-path tests:
- `test_tool_registry_register` - Register a tool and verify it's in the registry
- `test_tool_registry_register_handler` - Use register_handler method
- `test_tool_registry_get_handler` - Retrieve a registered handler by name
- `test_tool_registry_get_definition` - Get ToolDefinition with all fields
- `test_tool_registry_list_tools` - List all registered tools
- `test_tool_registry_is_registered` - Check if tool exists
- `test_tool_registry_tool_count` - Count registered tools
- `test_tool_router_route_tool_success` - Route to handler and get result
- `test_tool_router_get_policy_requirements` - Get policy for a tool
- `test_get_global_registry_singleton` - Verify singleton pattern
- `test_register_tool_decorator` - Use @register_tool decorator

#### Error-path tests:
- `test_tool_router_route_unknown_tool` - Raise ValueError for unknown tool
- `test_tool_registry_get_handler_not_found` - Return None for missing handler
- `test_get_handler_returns_none_for_unknown` - Verify None for unknown tools

### 2. Replace test_transport.py with real tests

**Source module: `src/hub/transport/mcp.py`**

#### Happy-path tests:
- `test_parse_tool_call_valid` - Parse valid MCP tools/call request
- `test_parse_tool_call_with_trace_id` - Extract trace_id from request
- `test_parse_tool_call_with_message_id` - Extract message_id for correlation
- `test_parse_tool_call_with_arguments` - Extract parameters from arguments dict
- `test_format_tool_response_success` - Format successful response
- `test_format_tool_response_with_trace_id` - Include trace_id in response
- `test_format_tool_response_with_message_id` - Include message_id for correlation
- `test_format_tool_response_with_duration` - Include duration_ms
- `test_format_tool_list` - Format tool list for MCP
- `test_mcp_transport_send` - Send message via transport

#### Error-path tests:
- `test_parse_tool_call_invalid_method` - Raise TransportError for non-tools/call
- `test_parse_tool_call_missing_name` - Raise TransportError when name missing
- `test_format_tool_response_error` - Format error response correctly

### 3. Replace test_executor.py with real tests

**Source module: `src/node_agent/executor.py`**

#### Happy-path tests:
- `test_executor_init_with_allowed_paths` - Initialize with path list
- `test_executor_validate_path_within_allowed` - Allow path inside boundary
- `test_executor_list_directory` - List directory contents with metadata
- `test_executor_list_directory_max_entries` - Respects max_entries limit
- `test_executor_read_file` - Read file with offset/limit
- `test_executor_read_file_truncation` - Verify truncated flag
- `test_executor_search_files_text_mode` - Search in text mode
- `test_executor_search_files_path_mode` - Search in path mode
- `test_executor_search_files_symbol_mode` - Search in symbol mode
- `test_executor_search_files_no_matches` - Handle no matches gracefully
- `test_executor_git_status` - Get git status with all fields
- `test_executor_git_status_recent_commits` - Verify recent_commits field
- `test_executor_write_file_create` - Create new file with atomic write
- `test_executor_write_file_overwrite` - Overwrite existing file
- `test_executor_write_file_verification` - Verify SHA256 in response

#### Error-path tests:
- `test_executor_validate_path_outside_allowed` - Reject path outside boundary
- `test_executor_validate_path_no_allowed` - Deny all when no paths configured
- `test_executor_validate_path_traversal` - Reject path traversal attempts
- `test_executor_list_directory_not_dir` - Raise ValueError for non-directory
- `test_executor_read_file_not_file` - Raise ValueError for non-file
- `test_executor_read_file_not_utf8` - Raise ValueError for binary files
- `test_executor_write_file_no_overwrite` - Raise FileExistsError in no_overwrite mode

### 4. Replace test_logging.py with real tests

**Source modules: `src/shared/logging.py`, `src/shared/context.py`**

#### Happy-path tests:
- `test_redact_sensitive_dict` - Redact password/secret/token fields
- `test_redact_sensitive_nested` - Redact nested sensitive fields
- `test_redact_sensitive_list` - Redact in lists
- `test_redact_sensitive_no_match` - Pass through non-sensitive data
- `test_redact_sensitive_long_string` - Truncate very long strings
- `test_structured_logger_info` - Log with context
- `test_structured_logger_error` - Log errors with context
- `test_structured_logger_set_context` - Set context for multiple logs
- `test_structured_logger_clear_context` - Clear context
- `test_trace_id_get_set` - Get and set trace ID
- `test_trace_id_generate` - Generate new trace ID
- `test_trace_context_sync` - Sync context manager
- `test_trace_context_async` - Async context manager
- `test_trace_context_propagates_across_async` - Propagate across await
- `test_trace_context_class` - TraceContext class usage
- `test_json_formatter_includes_trace_id` - Trace ID in JSON output
- `test_text_formatter_includes_trace_id` - Trace ID in text output

#### Error-path tests:
- `test_redact_sensitive_max_depth` - Handle deep nesting gracefully
- `test_trace_context_restores_on_error` - Restore state after exception

## Validation Plan

1. **Syntax validation**: Run `python3 -m py_compile` on all modified test files
2. **Import validation**: Verify all imports resolve correctly
3. **Test discovery**: Run `pytest --collect-only` to verify tests are discoverable
4. **Coverage**: Run tests with `pytest -v` and verify no failures
5. **Placeholder removal verification**: Use grep to ensure no `assert True`, `pass`, or `TODO` remain in test bodies

## Risks and Assumptions

### Assumptions
- All source files exist and are importable (verified via file reads)
- pytest and pytest-asyncio are available for async test execution
- Tests can create temporary files/directories for executor tests

### Risks
- Executor tests require file system access - may need tmpdir fixture
- Transport tests may need mock for request data
- Logging tests may need caplog fixture for log capture

## Blockers

None - all source files are readable and test patterns are well-defined.

## Test Patterns to Follow

Based on existing tests in the repo (e.g., `tests/hub/test_contracts.py`, `tests/hub/test_security.py`):

```python
import pytest
from src.hub.tool_router import ToolRegistry, ToolDefinition

@pytest.fixture
def registry():
    return ToolRegistry()

async def mock_handler(**kwargs):
    return {"result": "success"}

def test_tool_registration(registry):
    """Test tool registration."""
    definition = ToolDefinition(
        name="test_tool",
        description="A test tool",
        handler=mock_handler,
    )
    registry.register(definition)
    assert registry.is_registered("test_tool")
    assert registry.tool_count == 1
```

## Summary of Test Cases

| File | Happy-path tests | Error-path tests | Total |
|------|-----------------|------------------|-------|
| test_routing.py | 11 | 3 | 14 |
| test_transport.py | 10 | 3 | 13 |
| test_executor.py | 15 | 7 | 22 |
| test_logging.py | 16 | 2 | 18 |
| **Total** | **52** | **15** | **67** |

All placeholder tests (assert True, pass) will be removed and replaced with these comprehensive test cases.

# Smoke Test

## Ticket

- REMED-001

## Overall Result

Overall Result: PASS

## Notes

All detected deterministic smoke-test commands passed.

## Commands

### 1. command override 1

- reason: Explicit smoke-test command override supplied by the caller.
- command: `UV_CACHE_DIR=/tmp/uv-cache uv run python -c from src.hub.main import app`
- exit_code: 0
- duration_ms: 1090
- missing_executable: none
- failure_classification: none
- blocked_by_permissions: false

#### stdout

~~~~text
<no output>
~~~~

#### stderr

~~~~text
<no output>
~~~~

### 2. command override 2

- reason: Explicit smoke-test command override supplied by the caller.
- command: `UV_CACHE_DIR=/tmp/uv-cache uv run python -c from src.node_agent.main import app`
- exit_code: 0
- duration_ms: 393
- missing_executable: none
- failure_classification: none
- blocked_by_permissions: false

#### stdout

~~~~text
<no output>
~~~~

#### stderr

~~~~text
<no output>
~~~~

### 3. command override 3

- reason: Explicit smoke-test command override supplied by the caller.
- command: `UV_CACHE_DIR=/tmp/uv-cache uv run python -c import src.shared.models; import src.shared.schemas`
- exit_code: 0
- duration_ms: 206
- missing_executable: none
- failure_classification: none
- blocked_by_permissions: false

#### stdout

~~~~text
<no output>
~~~~

#### stderr

~~~~text
<no output>
~~~~

### 4. command override 4

- reason: Explicit smoke-test command override supplied by the caller.
- command: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/hub/test_contracts.py tests/hub/test_transport.py tests/node_agent/test_executor.py --collect-only -q`
- exit_code: 0
- duration_ms: 1452
- missing_executable: none
- failure_classification: none
- blocked_by_permissions: false

#### stdout

~~~~text
tests/hub/test_contracts.py::TestDiscoveryTools::test_list_nodes_returns_structured_response
tests/hub/test_contracts.py::TestDiscoveryTools::test_list_nodes_empty_registry
tests/hub/test_contracts.py::TestDiscoveryTools::test_list_nodes_no_repository
tests/hub/test_contracts.py::TestDiscoveryTools::test_list_repos_returns_structured_response
tests/hub/test_contracts.py::TestDiscoveryTools::test_list_repos_filtered_by_node
tests/hub/test_contracts.py::TestDiscoveryTools::test_list_repos_no_repository
tests/hub/test_contracts.py::TestInspectionTools::test_inspect_repo_tree_requires_node_and_repo
tests/hub/test_contracts.py::TestInspectionTools::test_inspect_repo_tree_node_not_found
tests/hub/test_contracts.py::TestInspectionTools::test_inspect_repo_tree_success
tests/hub/test_contracts.py::TestInspectionTools::test_read_repo_file_requires_parameters
tests/hub/test_contracts.py::TestInspectionTools::test_read_repo_file_success
tests/hub/test_contracts.py::TestInspectionTools::test_read_repo_file_path_traversal_rejected
tests/hub/test_contracts.py::TestSearchTools::test_search_repo_validates_parameters
tests/hub/test_contracts.py::TestSearchTools::test_search_repo_success
tests/hub/test_contracts.py::TestSearchTools::test_search_repo_max_results_clamped
tests/hub/test_contracts.py::TestSearchTools::test_git_status_returns_proper_format
tests/hub/test_contracts.py::TestSearchTools::test_git_status_node_not_found
tests/hub/test_contracts.py::TestWriteTools::test_write_markdown_validates_extension
tests/hub/test_contracts.py::TestWriteTools::test_write_markdown_requires_write_target
tests/hub/test_contracts.py::TestWriteTools::test_write_markdown_success
tests/hub/test_contracts.py::TestWriteTools::test_write_markdown_path_traversal_rejected
tests/hub/test_contracts.py::TestLLMTools::test_chat_llm_requires_service_alias
tests/hub/test_contracts.py::TestLLMTools::test_chat_llm_requires_prompt
tests/hub/test_contracts.py::TestLLMTools::test_chat_llm_returns_structured_response
tests/hub/test_contracts.py::TestLLMTools::test_chat_llm_invalid_service_rejected
tests/hub/test_contracts.py::TestLLMTools::test_chat_llm_with_task_routing
tests/hub/test_contracts.py::TestFailureModes::test_unknown_node_rejected
tests/hub/test_contracts.py::TestFailureModes::test_unknown_repo_rejected
tests/hub/test_contracts.py::TestFailureModes::test_invalid_path_rejected
tests/hub/test_contracts.py::TestFailureModes::test_missing_required_params_rejected
tests/hub/test_contracts.py::TestFailureModes::test_node_client_not_available
tests/hub/test_contracts.py::TestFailureModes::test_repository_not_available
tests/hub/test_transport.py::test_parse_tool_call_valid
tests/hub/test_transport.py::test_parse_tool_call_with_trace_id
tests/hub/test_transport.py::test_parse_tool_call_with_message_id
tests/hub/test_transport.py::test_parse_tool_call_with_arguments
tests/hub/test_transport.py::test_format_tool_response_success
tests/hub/test_transport.py::test_format_tool_response_with_trace_id
tests/hub/test_transport.py::test_format_tool_response_with_message_id
tests/hub/test_transport.py::test_format_tool_response_with_duration
tests/hub/test_transport.py::test_format_tool_list
tests/hub/test_transport.py::test_mcp_transport_send
tests/hub/test_transport.py::test_parse_tool_call_invalid_method
tests/hub/test_transport.py::test_parse_tool_call_missing_name
tests/hub/test_transport.py::test_format_tool_response_error
tests/node_agent/test_executor.py::test_executor_init_with_allowed_paths
tests/node_agent/test_executor.py::test_executor_validate_path_within_allowed
tests/node_agent/test_executor.py::test_executor_list_directory
tests/node_agent/test_executor.py::test_executor_list_directory_max_entries
tests/node_agent/test_executor.py::test_executor_read_file
tests/node_agent/test_executor.py::test_executor_read_file_truncation
tests/node_agent/test_executor.py::test_executor_search_files_text_mode
tests/node_agent/test_executor.py::test_executor_search_files_path_mode
tests/node_agent/test_executor.py::test_executor_search_files_symbol_mode
tests/node_agent/test_executor.py::test_executor_search_files_no_matches
tests/node_agent/test_executor.py::test_executor_git_status
tests/node_agent/test_executor.py::test_executor_git_status_recent_commits
tests/node_agent/test_executor.py::test_executor_write_file_create
tests/node_agent/test_executor.py::test_executor_write_file_overwrite
tests/node_agent/test_executor.py::test_executor_write_file_verification
tests/node_agent/test_executor.py::test_executor_validate_path_outside_allowed
tests/node_agent/test_executor.py::test_executor_validate_path_no_allowed
tests/node_agent/test_executor.py::test_executor_validate_path_traversal
tests/node_agent/test_executor.py::test_executor_list_directory_not_dir
tests/node_agent/test_executor.py::test_executor_read_file_not_file
tests/node_agent/test_executor.py::test_executor_read_file_not_utf8
tests/node_agent/test_executor.py::test_executor_write_file_no_overwrite

67 tests collected in 0.69s
~~~~

#### stderr

~~~~text
<no output>
~~~~

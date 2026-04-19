# Smoke Test

## Ticket

- REMED-019

## Overall Result

Overall Result: PASS

## Notes

All detected deterministic smoke-test commands passed.

## Commands

### 1. qa artifact command 1

- reason: Current QA artifact records a deterministic smoke-test command.
- command: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest --collect-only -q`
- exit_code: 0
- duration_ms: 2658
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
tests/hub/test_routing.py::test_tool_registry_register
tests/hub/test_routing.py::test_tool_registry_register_handler
tests/hub/test_routing.py::test_tool_registry_get_handler
tests/hub/test_routing.py::test_tool_registry_get_definition
tests/hub/test_routing.py::test_tool_registry_list_tools
tests/hub/test_routing.py::test_tool_registry_is_registered
tests/hub/test_routing.py::test_tool_registry_tool_count
tests/hub/test_routing.py::test_tool_router_route_tool_success
tests/hub/test_routing.py::test_tool_router_get_policy_requirements
tests/hub/test_routing.py::test_get_global_registry_singleton
tests/hub/test_routing.py::test_register_tool_decorator
tests/hub/test_routing.py::test_tool_router_route_unknown_tool
tests/hub/test_routing.py::test_tool_registry_get_handler_not_found
tests/hub/test_routing.py::test_get_handler_returns_none_for_unknown
tests/hub/test_security.py::TestPathTraversal::test_path_traversal_dotdot_rejected
tests/hub/test_security.py::TestPathTraversal::test_path_traversal_windows_backslash_rejected
tests/hub/test_security.py::TestPathTraversal::test_path_traversal_absolute_path_rejected
tests/hub/test_security.py::TestPathTraversal::test_relative_path_within_base_accepted
tests/hub/test_security.py::TestPathTraversal::test_path_traversal_null_byte_rejected
tests/hub/test_security.py::TestPathTraversal::test_path_traversal_symlink_rejected
tests/hub/test_security.py::TestTargetValidation::test_unknown_node_access_denied
tests/hub/test_security.py::TestTargetValidation::test_unknown_repo_access_denied
tests/hub/test_security.py::TestTargetValidation::test_unregistered_write_target_denied
tests/hub/test_security.py::TestTargetValidation::test_extension_allowlist_enforced
tests/hub/test_security.py::TestRedaction::test_api_key_redacted_in_logs
tests/hub/test_security.py::TestRedaction::test_token_redacted_in_logs
tests/hub/test_security.py::TestRedaction::test_password_redacted_in_logs
tests/hub/test_security.py::TestRedaction::test_sensitive_path_redacted
tests/hub/test_security.py::TestRedaction::test_redaction_patterns_defined
tests/hub/test_security.py::TestFailClosed::test_missing_policy_engine_fails_closed
tests/hub/test_security.py::TestFailClosed::test_missing_repository_fails_closed
tests/hub/test_security.py::TestFailClosed::test_invalid_policy_requirement_denied
tests/hub/test_security.py::TestFailClosed::test_malformed_parameters_rejected
tests/hub/test_security.py::TestFailClosed::test_policy_engine_validates_before_execution
tests/hub/test_security.py::TestFailClosed::test_policy_engine_rejects_unknown_node
tests/hub/test_security.py::TestSecurityEdgeCases::test_url_encoded_traversal_rejected
tests/hub/test_security.py::TestSecurityEdgeCases::test_home_directory_expansion_rejected
tests/hub/test_security.py::TestSecurityEdgeCases::test_sensitive_pattern_case_insensitive
tests/hub/test_security.py::TestSecurityEdgeCases::test_health_unknown_fails_closed
tests/hub/test_security.py::TestSecurityEdgeCases::test_health_unhealthy_fails_closed
tests/hub/test_security.py::TestSecurityEdgeCases::test_list_redaction_handles_lists
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
tests/hub/test_tunnel_manager.py::test_build_command_uses_public_url_when_present
tests/hub/test_tunnel_manager.py::test_build_command_omits_public_url_when_not_configured
tests/hub/test_tunnel_manager.py::test_health_check_reports_disabled_state
tests/hub/test_tunnel_manager.py::test_health_check_reports_external_management
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
tests/shared/test_logging.py::test_redact_sensitive_dict
tests/shared/test_logging.py::test_redact_sensitive_nested
tests/shared/test_logging.py::test_redact_sensitive_list
tests/shared/test_logging.py::test_redact_sensitive_no_match
tests/shared/test_logging.py::test_redact_sensitive_long_string
tests/shared/test_logging.py::test_structured_logger_info
tests/shared/test_logging.py::test_structured_logger_error
tests/shared/test_logging.py::test_structured_logger_set_context
tests/shared/test_logging.py::test_structured_logger_clear_context
tests/shared/test_logging.py::test_trace_id_get_set
tests/shared/test_logging.py::test_trace_id_generate
tests/shared/test_logging.py::test_trace_context_sync
tests/shared/test_logging.py::test_trace_context_async
tests/shared/test_logging.py::test_trace_context_propagates_across_async
tests/shared/test_logging.py::test_trace_context_class
tests/shared/test_logging.py::test_json_formatter_includes_trace_id
tests/shared/test_logging.py::test_text_formatter_includes_trace_id
tests/shared/test_logging.py::test_redact_sensitive_max_depth
tests/shared/test_logging.py::test_trace_context_restores_on_error

131 tests collected in 1.27s
~~~~

#### stderr

~~~~text
<no output>
~~~~

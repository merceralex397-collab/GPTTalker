"""Tests for MCP transport layer."""

import pytest

from src.hub.transport.base import TransportError, TransportResult, TransportStatus
from src.hub.transport.mcp import (
    MCPTransport,
    format_tool_list,
    format_tool_response,
    parse_tool_call,
)


# =============================================================================
# Happy-path tests
# =============================================================================


def test_parse_tool_call_valid():
    """Test parsing a valid MCP tools/call request."""
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "list_repos",
            "arguments": {"node_id": "node-1"},
        },
    }

    result = parse_tool_call(request)

    assert result["tool_name"] == "list_repos"
    assert result["parameters"] == {"node_id": "node-1"}
    assert result["message_id"] == 1


def test_parse_tool_call_with_trace_id():
    """Test extracting trace_id from request."""
    request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "test_tool",
            "arguments": {},
        },
        "trace_id": "trace-abc123",
    }

    result = parse_tool_call(request)

    assert result["trace_id"] == "trace-abc123"


def test_parse_tool_call_with_message_id():
    """Test extracting message_id for correlation."""
    request = {
        "jsonrpc": "2.0",
        "id": "msg-456",
        "method": "tools/call",
        "params": {
            "name": "test_tool",
            "arguments": {},
        },
    }

    result = parse_tool_call(request)

    assert result["message_id"] == "msg-456"


def test_parse_tool_call_with_arguments():
    """Test extracting parameters from arguments dict."""
    request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "search_repo",
            "arguments": {
                "repo_id": "repo-1",
                "pattern": "class.*Model",
                "mode": "text",
            },
        },
    }

    result = parse_tool_call(request)

    assert result["tool_name"] == "search_repo"
    assert result["parameters"]["repo_id"] == "repo-1"
    assert result["parameters"]["pattern"] == "class.*Model"
    assert result["parameters"]["mode"] == "text"


def test_format_tool_response_success():
    """Test formatting a successful tool response."""
    result = {"data": "test result"}

    response = format_tool_response(result)

    assert response["jsonrpc"] == "2.0"
    assert response["result"]["success"] is True
    assert response["result"]["data"] == "test result"
    assert "duration_ms" in response["result"]


def test_format_tool_response_with_trace_id():
    """Test including trace_id in response."""
    result = {"status": "ok"}

    response = format_tool_response(result, trace_id="trace-xyz789")

    assert response["trace_id"] == "trace-xyz789"


def test_format_tool_response_with_message_id():
    """Test including message_id for correlation."""
    result = {"output": "test"}

    response = format_tool_response(result, message_id="req-123")

    assert response["id"] == "req-123"


def test_format_tool_response_with_duration():
    """Test including duration_ms in response."""
    result = {"computation": "done"}

    response = format_tool_response(result, duration_ms=150)

    assert response["result"]["duration_ms"] == 150


def test_format_tool_list():
    """Test formatting tool list for MCP."""
    tools = [
        {
            "name": "list_repos",
            "description": "List repositories",
            "parameters": {"type": "object"},
        },
        {
            "name": "read_file",
            "description": "Read a file",
            "parameters": {"type": "object", "properties": {}},
        },
    ]

    response = format_tool_list(tools)

    assert response["jsonrpc"] == "2.0"
    assert "result" in response
    assert len(response["result"]["tools"]) == 2
    assert response["result"]["tools"][0]["name"] == "list_repos"
    assert response["result"]["tools"][0]["inputSchema"] == {"type": "object"}


@pytest.mark.asyncio
async def test_mcp_transport_send():
    """Test sending a message via MCP transport."""
    transport = MCPTransport()
    message = {"jsonrpc": "2.0", "method": "test"}

    result = await transport.send(message)

    assert result.is_success
    assert result.status == TransportStatus.SUCCESS
    assert result.data == message


# =============================================================================
# Error-path tests
# =============================================================================


def test_parse_tool_call_invalid_method():
    """Test that non-tools/call method raises TransportError."""
    request = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": {},
    }

    with pytest.raises(TransportError, match="Unsupported MCP method"):
        parse_tool_call(request)


def test_parse_tool_call_missing_name():
    """Test that missing name parameter raises TransportError."""
    request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "arguments": {},
        },
    }

    with pytest.raises(TransportError, match="Missing required parameter"):
        parse_tool_call(request)


def test_format_tool_response_error():
    """Test formatting an error response correctly."""
    response = format_tool_response(None, error="Tool execution failed")

    assert "error" in response
    assert response["error"]["code"] == -32603
    assert response["error"]["message"] == "Tool execution failed"
    assert "result" not in response

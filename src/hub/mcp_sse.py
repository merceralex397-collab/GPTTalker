"""MCP Server-Sent Events (SSE) transport for official MCP protocol support."""

import asyncio
import json
import uuid
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from src.hub.handlers import mcp_handler
from src.shared.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

# Store active sessions
sessions: dict[str, asyncio.Queue] = {}


@router.get("/mcp/v1/sse")
async def mcp_sse_endpoint(request: Request):
    """MCP SSE endpoint for official MCP protocol support.

    This endpoint establishes a Server-Sent Events connection
    for ChatGPT's native MCP Apps feature.
    """
    session_id = str(uuid.uuid4())
    message_queue: asyncio.Queue = asyncio.Queue()
    sessions[session_id] = message_queue

    logger.info(f"MCP SSE session established", extra={"session_id": session_id})

    async def event_generator():
        try:
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break

                # Get message from queue (non-blocking with timeout)
                try:
                    message = await asyncio.wait_for(message_queue.get(), timeout=1.0)
                    yield {"event": "message", "data": json.dumps(message)}
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield {"event": "keepalive", "data": ""}

        except Exception as e:
            logger.error(f"MCP SSE error: {e}", extra={"session_id": session_id})
        finally:
            if session_id in sessions:
                del sessions[session_id]
            logger.info(f"MCP SSE session closed", extra={"session_id": session_id})

    return EventSourceResponse(event_generator())


@router.post("/mcp/v1/message")
async def mcp_message_endpoint(request: Request):
    """Receive JSON-RPC messages from MCP clients.

    ChatGPT sends tool calls here, and we route them to handlers.
    """
    body = await request.json()

    # Parse JSON-RPC request
    jsonrpc = body.get("jsonrpc")
    method = body.get("method")
    params = body.get("params", {})
    request_id = body.get("id")

    logger.info(f"MCP message received", extra={"method": method, "id": request_id})

    response = {"jsonrpc": "2.0", "id": request_id}

    try:
        if method == "initialize":
            # MCP initialization handshake
            response["result"] = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "GPTTalker", "version": "1.0.0"},
            }

        elif method == "tools/list":
            # List available tools
            tools_result = await mcp_handler.list_tools()
            response["result"] = tools_result.get("result", {"tools": []})

        elif method == "tools/call":
            # Execute a tool
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            # Call the handler
            result = await mcp_handler.handle_tool_call(
                tool_name=tool_name, parameters=arguments, trace_id=str(uuid.uuid4())
            )

            # Format result properly
            if "error" in result:
                response["error"] = {
                    "code": -32603,
                    "message": result["error"].get("message", "Tool execution failed"),
                }
            else:
                response["result"] = {
                    "content": [
                        {"type": "text", "text": json.dumps(result.get("result", {}), indent=2)}
                    ],
                    "isError": False,
                }
        else:
            response["error"] = {"code": -32601, "message": f"Method not found: {method}"}

    except Exception as e:
        logger.error(f"MCP message error: {e}", extra={"method": method})
        response["error"] = {"code": -32603, "message": str(e)}

    return response

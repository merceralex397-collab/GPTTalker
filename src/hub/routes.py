"""Hub API routes."""

import time
from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from src.hub.dependencies import check_database_health
from src.hub.handlers import mcp_handler

router = APIRouter()


# --- MCP Request/Response Models ---


class MCPToolCallRequest(BaseModel):
    """Request model for MCP tool calls."""

    tool_name: str
    parameters: dict[str, Any] = {}
    trace_id: str | None = None


class MCPToolCallResponse(BaseModel):
    """Response model for MCP tool calls."""

    success: bool
    result: Any = None
    error: str | None = None
    trace_id: str | None = None
    duration_ms: int


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    service: str
    database: dict[str, Any] | None = None


# --- MCP Tool Endpoints ---


@router.get("/mcp/v1/tools")
async def list_tools():
    """List all available MCP tools.

    Returns a list of all registered tool definitions including
    their names, descriptions, and parameter schemas.
    """
    return await mcp_handler.list_tools()


@router.post("/mcp/v1/tools/call")
async def call_tool(request: MCPToolCallRequest, req: Request):
    """Execute an MCP tool call.

    Routes the tool call to the appropriate registered handler,
    validates parameters, and returns the result.

    Args:
        request: Tool call request with tool_name, parameters, and optional trace_id.
        req: FastAPI Request object to access app state for db_manager.

    Returns:
        Tool execution result with success status, data, and duration.
    """
    start_time = int(time.time() * 1000)

    # Get db_manager from app state if available
    db_manager = None
    if hasattr(req.app.state, "db_manager"):
        db_manager = req.app.state.db_manager

    try:
        result = await mcp_handler.handle_tool_call(
            tool_name=request.tool_name,
            parameters=request.parameters,
            trace_id=request.trace_id,
            db_manager=db_manager,
        )

        # Extract success from result
        success = result.get("result", {}).get("success", False) if "result" in result else False

        return MCPToolCallResponse(
            success=success,
            result=result.get("result", {}).get("data") if "result" in result else None,
            error=result.get("error", {}).get("message") if "error" in result else None,
            trace_id=request.trace_id,
            duration_ms=int(time.time() * 1000) - start_time,
        )
    except Exception as e:
        return MCPToolCallResponse(
            success=False,
            error=str(e),
            trace_id=request.trace_id,
            duration_ms=int(time.time() * 1000) - start_time,
        )


@router.get("/mcp/v1/health")
async def mcp_health():
    """MCP-specific health check endpoint.

    Returns the health status from the MCP handler perspective.
    """
    return {
        "status": "healthy",
        "service": "gpttalker-mcp",
        "version": "1.0",
    }


# --- Health Endpoint ---


@router.get("/health", response_model=HealthResponse)
async def health_check(db_health: dict[str, Any] = Depends(check_database_health)):
    """Health check endpoint for the hub service.

    Returns basic health status including database connectivity.
    """
    return HealthResponse(
        status="healthy",
        service="gpttalker-hub",
        database=db_health,
    )


# --- Future Tool Endpoints (Commented for Reference) ---


# TODO(REPO-001): Add list_nodes endpoint
# TODO(REPO-001): Add list_repos endpoint
# TODO(REPO-002): Add inspect_repo_tree endpoint
# TODO(REPO-002): Add read_repo_file endpoint
# TODO(REPO-003): Add search_repo endpoint
# TODO(REPO-003): Add git_status endpoint
# TODO(WRITE-001): Add write_markdown endpoint
# TODO(LLM-001): Add chat_llm endpoint
# TODO(CTX-002): Add index_repo endpoint
# TODO(CTX-003): Add get_project_context endpoint
# TODO(OBS-001): Add task history endpoints

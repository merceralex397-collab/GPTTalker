"""Hub main application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.hub.config import get_hub_config
from src.hub.lifespan import lifespan
from src.hub.mcp import MCPProtocolHandler
from src.hub.routes import router
from src.hub.tool_router import get_global_registry
from src.shared.logging import get_logger
from src.shared.middleware import setup_middleware

# Initialize logger
logger = get_logger(__name__)

# Get configuration for CORS origins
config = get_hub_config()

# Parse CORS origins from environment (comma-separated)
cors_origins = getattr(config, "cors_origins", None)
if cors_origins:
    # Handle comma-separated list or JSON array
    if isinstance(cors_origins, str):
        if cors_origins.startswith("["):
            import json

            cors_origins = json.loads(cors_origins)
        else:
            cors_origins = [o.strip() for o in cors_origins.split(",") if o.strip()]
else:
    # Default: allow all for development
    cors_origins = ["*"]

app = FastAPI(
    title="GPTTalker Hub",
    description="Lightweight MCP hub for safe multi-machine development environment access",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up exception handlers
setup_middleware(app)

# Include API routes
app.include_router(router)


@app.on_event("startup")
async def register_tools():
    """Register MCP tools on application startup."""
    from src.hub.tools import register_all_tools

    registry = get_global_registry()
    register_all_tools(registry)
    logger.info("tools_registered", tool_count=registry.tool_count)


@app.get("/health")
async def health_check():
    """Health check endpoint for the hub service.

    Returns basic health status including database connectivity.
    """
    # Get db health from dependency
    db_health = {"status": "unknown", "connected": False}

    # Try to get database state from app
    if hasattr(app.state, "db_manager") and app.state.db_manager is not None:
        try:
            await app.state.db_manager.connection.execute("SELECT 1")
            db_health = {"status": "healthy", "connected": True}
        except Exception as e:
            db_health = {"status": "unhealthy", "connected": False, "error": str(e)}

    return {
        "status": "healthy",
        "service": "gpttalker-hub",
        "database": db_health,
    }


# Initialize MCP handler (will be used by routes)
mcp_handler = MCPProtocolHandler()

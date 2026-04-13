"""Hub main application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.hub.config import get_hub_config
from src.hub.lifespan import lifespan
from src.hub.routes import router
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

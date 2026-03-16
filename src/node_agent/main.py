"""Node agent service entrypoint."""

import uvicorn
from fastapi import FastAPI

from src.node_agent.lifespan import lifespan
from src.node_agent.routes import health, operations


def create_app() -> FastAPI:
    """Create and configure the FastAPI application for the node agent.

    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title="GPTTalker Node Agent",
        description="Lightweight agent service for local repo operations",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Register routes
    app.include_router(health.router, tags=["health"])
    app.include_router(operations.router, tags=["operations"])

    return app


# Create app instance for uvicorn
app = create_app()


def run() -> None:
    """Run the node agent service."""
    uvicorn.run(
        "src.node_agent.main:app",
        host="0.0.0.0",
        port=8080,
        reload=False,
    )


if __name__ == "__main__":
    run()

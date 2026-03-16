"""Pytest fixtures for GPTTalker tests."""

import os
import sys
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock

import aiosqlite
import pytest
from fastapi.testclient import TestClient

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# ============================================================================
# Configuration Fixtures
# ============================================================================


@pytest.fixture
def mock_config():
    """Mock configuration fixture."""

    class MockConfig:
        log_level = "DEBUG"
        log_format = "json"

    return MockConfig()


@pytest.fixture
def hub_config():
    """Hub configuration fixture."""

    class HubConfig:
        host = "127.0.0.1"
        port = 8000
        database_url = "sqlite+aiosqlite:///:memory:"
        qdrant_host = "localhost"
        qdrant_port = 6333

    return HubConfig()


@pytest.fixture
def node_agent_config():
    """Node agent configuration fixture."""

    class NodeAgentConfig:
        node_name = "test-node"
        hub_url = "http://127.0.0.1:8000"
        allowed_repos = ["/tmp/test_repos"]
        allowed_write_targets = ["/tmp/test_writes"]

    return NodeAgentConfig()


# ============================================================================
# Async Database Fixtures
# ============================================================================


@pytest.fixture
async def async_db_session() -> AsyncGenerator[aiosqlite.Connection, None]:
    """Create a fresh async database session for each test.

    Uses an in-memory SQLite database and applies schema migrations.
    """
    async with aiosqlite.connect(":memory:") as db:
        # Enable foreign keys
        await db.execute("PRAGMA foreign_keys = ON")

        # Create schema tables (mirrors SETUP-003)
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_name TEXT NOT NULL UNIQUE,
                tailnet_ip TEXT,
                status TEXT NOT NULL DEFAULT 'offline',
                last_health_check TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS repos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_id INTEGER NOT NULL,
                repo_name TEXT NOT NULL,
                repo_path TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                last_indexed TEXT,
                content_hash TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (node_id) REFERENCES nodes(id) ON DELETE CASCADE,
                UNIQUE(node_id, repo_path)
            );

            CREATE TABLE IF NOT EXISTS write_targets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_id INTEGER NOT NULL,
                target_path TEXT NOT NULL,
                allowed_extensions TEXT NOT NULL DEFAULT '.md,.txt',
                created_at TEXT NOT NULL,
                FOREIGN KEY (node_id) REFERENCES nodes(id) ON DELETE CASCADE,
                UNIQUE(node_id, target_path)
            );

            CREATE TABLE IF NOT EXISTS llm_services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_name TEXT NOT NULL UNIQUE,
                service_type TEXT NOT NULL,
                endpoint TEXT,
                api_key_env_var TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_type TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                caller TEXT NOT NULL,
                target_node_id INTEGER,
                target_repo_id INTEGER,
                status TEXT NOT NULL DEFAULT 'pending',
                input_summary TEXT,
                output_summary TEXT,
                error_message TEXT,
                trace_id TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                duration_ms INTEGER,
                FOREIGN KEY (target_node_id) REFERENCES nodes(id),
                FOREIGN KEY (target_repo_id) REFERENCES repos(id)
            );

            CREATE TABLE IF NOT EXISTS issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repo_id INTEGER NOT NULL,
                issue_type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                severity TEXT NOT NULL DEFAULT 'low',
                status TEXT NOT NULL DEFAULT 'open',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                resolved_at TEXT,
                FOREIGN KEY (repo_id) REFERENCES repos(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_tasks_trace_id ON tasks(trace_id);
            CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
            CREATE INDEX IF NOT EXISTS idx_repos_node_id ON repos(node_id);
            CREATE INDEX IF NOT EXISTS idx_issues_repo_id ON issues(repo_id);
        """)

        await db.commit()
        yield db


# ============================================================================
# FastAPI Test Client Fixtures
# ============================================================================


@pytest.fixture
def test_client() -> Generator[TestClient, None, None]:
    """Provide a FastAPI TestClient for hub endpoint testing.

    Note: This creates a basic test client. For full integration tests,
    import the actual app from src.hub.main in your test files.
    """
    # Import here to avoid circular imports
    from fastapi import FastAPI

    app = FastAPI(title="GPTTalker Test App")

    @app.get("/health")
    def health_check():
        return {"status": "ok"}

    with TestClient(app) as client:
        yield client


# ============================================================================
# Mock Registry Fixtures
# ============================================================================


@pytest.fixture
def mock_node_registry():
    """Provide a mock node registry for testing node-related flows."""
    mock_registry = MagicMock()
    mock_registry.list_nodes = MagicMock(
        return_value=[
            {
                "id": 1,
                "node_name": "test-node-1",
                "tailnet_ip": "100.64.0.1",
                "status": "online",
                "last_health_check": "2026-03-16T10:00:00Z",
            },
            {
                "id": 2,
                "node_name": "test-node-2",
                "tailnet_ip": "100.64.0.2",
                "status": "offline",
                "last_health_check": None,
            },
        ]
    )
    mock_registry.get_node = MagicMock(
        return_value={
            "id": 1,
            "node_name": "test-node-1",
            "tailnet_ip": "100.64.0.1",
            "status": "online",
        }
    )
    return mock_registry


@pytest.fixture
def mock_qdrant_client():
    """Provide a mock Qdrant client for context tests."""
    mock_client = MagicMock()
    mock_client.search = MagicMock(
        return_value=[
            {
                "id": "doc1",
                "score": 0.95,
                "payload": {
                    "repo_name": "test-repo",
                    "file_path": "README.md",
                    "content": "Test content",
                },
            }
        ]
    )
    mock_client.get_collections = MagicMock(
        return_value={
            "collections": [
                {"name": "project_context", "vectors_count": 100},
            ]
        }
    )
    return mock_client


# ============================================================================
# Environment Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set up test environment variables."""
    monkeypatch.setenv("TEST_DB_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")

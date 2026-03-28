"""Shared package - common models, config, logging, and exceptions used by hub and node agent."""

from src.shared import exceptions, logging, models

# Database components
from src.shared.database import DatabaseManager, get_connection, get_db_manager, initialize_database
from src.shared.migrations import get_db_version, run_migrations

# Repository components
from src.shared.repositories import (
    IssueRepository,
    LLMServiceRepository,
    NodeRepository,
    RepoRepository,
    TaskRepository,
    WriteTargetRepository,
)
from src.shared.tables import SCHEMA_VERSION

__all__ = [
    # Base modules
    "models",
    "logging",
    "exceptions",
    # Database
    "DatabaseManager",
    "get_db_manager",
    "initialize_database",
    "get_connection",
    "run_migrations",
    "get_db_version",
    "SCHEMA_VERSION",
    # Repositories
    "NodeRepository",
    "RepoRepository",
    "WriteTargetRepository",
    "LLMServiceRepository",
    "TaskRepository",
    "IssueRepository",
]

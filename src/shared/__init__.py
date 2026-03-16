"""Shared package - common models, config, logging, and exceptions used by hub and node agent."""

from src.shared import exceptions, logging, models

# Database components
from src.shared.database import DatabaseManager, get_db_manager, initialize_database, get_connection
from src.shared.migrations import run_migrations, get_db_version
from src.shared.tables import SCHEMA_VERSION

# Repository components
from src.shared.repositories import (
    NodeRepository,
    RepoRepository,
    WriteTargetRepository,
    LLMServiceRepository,
    TaskRepository,
    IssueRepository,
)

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

"""Repo access policy with fail-closed validation."""

import os

from src.shared.logging import get_logger
from src.shared.models import RepoInfo
from src.shared.repositories.repos import RepoRepository

logger = get_logger(__name__)


class RepoPolicy:
    """Policy engine for repository access control.

    This policy enforces fail-closed behavior: unknown or invalid repositories
    are rejected by raising ValueError.
    """

    def __init__(self, repo_repo: RepoRepository):
        """Initialize with repo repository.

        Args:
            repo_repo: Repository for repo CRUD operations.
        """
        self._repo = repo_repo

    async def validate_repo_access(self, repo_id: str) -> RepoInfo:
        """Validate access to a repository.

        Args:
            repo_id: Repository identifier to validate.

        Returns:
            RepoInfo if repository exists and is accessible.

        Raises:
            ValueError: If repository is unknown or inaccessible.
        """
        repo = await self._repo.get(repo_id)
        if not repo:
            logger.warning("repo_access_denied", repo_id=repo_id, reason="unknown_repo")
            raise ValueError(f"Unknown repository: {repo_id}")

        logger.info("repo_access_granted", repo_id=repo_id)
        return repo

    async def validate_path_in_repo(self, repo_id: str, file_path: str) -> bool:
        """Validate that a file path is within a repository.

        Args:
            repo_id: Repository identifier.
            file_path: Absolute file path to validate.

        Returns:
            True if path is within the repo, False otherwise.
        """
        repo = await self._repo.get(repo_id)
        if not repo:
            return False

        # Normalize paths for comparison
        normalized_path = os.path.normpath(file_path)
        normalized_repo = os.path.normpath(repo.path)

        return normalized_path.startswith(normalized_repo)

    async def list_accessible_repos(self) -> list[RepoInfo]:
        """List all accessible repositories.

        Returns:
            List of all registered RepoInfo instances.
        """
        return await self._repo.list_all()

    async def list_repos_on_node(self, node_id: str) -> list[RepoInfo]:
        """List repositories on a specific node.

        Args:
            node_id: Node identifier to filter by.

        Returns:
            List of RepoInfo instances on the node.
        """
        return await self._repo.list_by_node(node_id)

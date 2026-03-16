"""Write target policy with fail-closed validation."""

from src.shared.logging import get_logger
from src.shared.models import WriteTargetInfo
from src.shared.repositories.write_targets import WriteTargetRepository

logger = get_logger(__name__)


class WriteTargetPolicy:
    """Policy engine for write target access control.

    This policy enforces fail-closed behavior: unknown paths or disallowed
    extensions are rejected by raising ValueError.
    """

    def __init__(self, write_repo: WriteTargetRepository):
        """Initialize with write target repository.

        Args:
            write_repo: Repository for write target CRUD operations.
        """
        self._repo = write_repo

    async def validate_write_access(self, path: str, extension: str) -> WriteTargetInfo:
        """Validate write access to a path.

        Args:
            path: Absolute path to write to.
            extension: File extension (e.g., '.md').

        Returns:
            WriteTargetInfo if path is allowed.

        Raises:
            ValueError: If path is unknown or extension not allowed.
        """
        target = await self._repo.get_by_path(path)
        if not target:
            logger.warning("write_access_denied", path=path, reason="unknown_target")
            raise ValueError(f"Unknown write target: {path}")

        if extension not in target.allowed_extensions:
            logger.warning(
                "write_access_denied",
                path=path,
                extension=extension,
                allowed=target.allowed_extensions,
                reason="extension_not_allowed",
            )
            raise ValueError(
                f"Extension '{extension}' not allowed. Allowed: {target.allowed_extensions}"
            )

        logger.info("write_access_granted", path=path, extension=extension)
        return target

    async def list_write_targets(self) -> list[WriteTargetInfo]:
        """List all registered write targets.

        Returns:
            List of all WriteTargetInfo instances.
        """
        return await self._repo.list_all()

    async def list_write_targets_for_repo(self, repo_id: str) -> list[WriteTargetInfo]:
        """List write targets for a specific repository.

        Args:
            repo_id: Repository identifier to filter by.

        Returns:
            List of WriteTargetInfo instances for the repo.
        """
        return await self._repo.list_by_repo(repo_id)

    def validate_extension(self, extension: str, allowed: list[str]) -> bool:
        """Validate a file extension against an allowlist.

        Args:
            extension: File extension to validate.
            allowed: List of allowed extensions.

        Returns:
            True if extension is allowed.
        """
        return extension in allowed

"""Bounded operation executor for node agent."""

from pathlib import Path


class OperationExecutor:
    """
    Executes bounded operations on the local machine.

    This executor restricts operations to allowed paths and enforces
    timeouts and resource limits.
    """

    def __init__(self, allowed_paths: list[str] | None = None):
        """
        Initialize the operation executor.

        Args:
            allowed_paths: List of allowed base paths for operations
        """
        self.allowed_paths = [Path(p).resolve() for p in (allowed_paths or [])]

    def _validate_path(self, path: str) -> Path:
        """
        Validate that a path is within allowed boundaries.

        Args:
            path: Path to validate

        Returns:
            Resolved absolute path

        Raises:
            PermissionError: If path is not within allowed boundaries
        """
        resolved = Path(path).resolve()

        # If no allowed paths specified, deny all
        if not self.allowed_paths:
            raise PermissionError("No allowed paths configured")

        # Check if path is under any allowed path
        for allowed in self.allowed_paths:
            try:
                resolved.relative_to(allowed)
                return resolved
            except ValueError:
                continue

        raise PermissionError(f"Path not within allowed boundaries: {path}")

    async def list_directory(self, path: str) -> list[str]:
        """
        List contents of a directory.

        Args:
            path: Directory path to list

        Returns:
            List of file/directory names
        """
        self._validate_path(path)
        # TODO(REPO-002): Implement bounded directory listing
        raise NotImplementedError("list_directory not yet implemented")

    async def read_file(self, path: str, offset: int = 0, limit: int | None = None) -> str:
        """
        Read contents of a file.

        Args:
            path: File path to read
            offset: Byte offset to start reading from
            limit: Maximum bytes to read

        Returns:
            File contents as string
        """
        self._validate_path(path)
        # TODO(REPO-002): Implement bounded file reading
        raise NotImplementedError("read_file not yet implemented")

    async def search_files(
        self,
        directory: str,
        pattern: str,
        include_patterns: list[str] | None = None,
    ) -> list[dict]:
        """
        Search for pattern in files within a directory.

        Args:
            directory: Directory to search in
            pattern: Search pattern (regex)
            include_patterns: File patterns to include (e.g., ["*.py", "*.md"])

        Returns:
            List of search results with file, line, and content
        """
        self._validate_path(directory)
        # TODO(REPO-003): Implement bounded search using ripgrep
        raise NotImplementedError("search_files not yet implemented")

    async def git_status(self, repo_path: str) -> dict:
        """
        Get git status for a repository.

        Args:
            repo_path: Path to the git repository

        Returns:
            Git status information
        """
        self._validate_path(repo_path)
        # TODO(REPO-003): Implement read-only git status
        raise NotImplementedError("git_status not yet implemented")

    async def write_file(self, path: str, content: str) -> dict:
        """
        Write content to a file (atomic write).

        Args:
            path: File path to write
            content: Content to write

        Returns:
            Write result with verification metadata
        """
        self._validate_path(path)
        # TODO(WRITE-001): Implement atomic write with verification
        raise NotImplementedError("write_file not yet implemented")

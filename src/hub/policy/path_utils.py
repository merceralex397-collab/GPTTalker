"""Path normalization utility for secure file operations.

This module provides centralized path normalization and validation to prevent:
- Path traversal attacks (..)
- Symlink escapes
- Absolute path injection
- Other path-based security issues
"""

from dataclasses import dataclass
from pathlib import Path

from src.shared.exceptions import PathTraversalError
from src.shared.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PathValidationResult:
    """Result of path validation operations.

    Attributes:
        normalized_path: The normalized path if valid.
        is_valid: Whether the path passed validation.
        error: Error message if validation failed.
    """

    normalized_path: str
    is_valid: bool
    error: str | None = None


class PathNormalizer:
    """Central path normalization and validation utility.

    Enforces:
    - No path traversal (..)
    - No symlink escapes
    - No absolute paths (relative to base)
    - Normalized separators
    """

    # Characters that indicate path traversal attempts
    TRAVERSAL_PATTERNS = ["..", "~"]

    # Allowed path separators
    PATH_SEPARATOR = "/"

    @staticmethod
    def normalize(path: str, base: str | None = None) -> str:
        """Normalize a path relative to base.

        Args:
            path: The path to normalize.
            base: Optional base directory to resolve relative paths against.

        Returns:
            Normalized path.

        Raises:
            PathTraversalError: If path escapes base or contains invalid patterns.
        """
        if not path:
            raise PathTraversalError("Path cannot be empty")

        # Strip whitespace
        path = path.strip()

        # Check for null byte injection
        if "\x00" in path:
            raise PathTraversalError(f"Null byte in path not allowed: '{path}'")

        # Check for home directory expansion BEFORE resolve() expands ~
        if "~" in path:
            raise PathTraversalError(
                f"Path traversal detected: home directory expansion '{path}' not allowed"
            )

        # Normalize the path - join with base first if provided
        try:
            if base:
                # Join path to base
                joined = str((Path(base) / path).as_posix())
                # Manually resolve .. components since resolve() doesn't work on non-existent paths
                parts = joined.split("/")
                stack = []
                for part in parts:
                    if part == "" or part == ".":
                        continue
                    elif part == "..":
                        if stack and stack[-1] != "..":
                            stack.pop()
                        else:
                            # Can't go up further, this is traversal
                            raise PathTraversalError(
                                f"Path traversal detected: '{path}' escapes base directory '{base}'"
                            )
                    else:
                        stack.append(part)
                normalized = "/" + "/".join(stack) if stack else "/"
            else:
                normalized = str(Path(path).resolve().as_posix())
        except (ValueError, OSError) as e:
            raise PathTraversalError(f"Invalid path: {path}") from e

        # Check for traversal patterns after normalization (.. resolved by join)
        PathNormalizer.validate_no_traversal(normalized)

        # If base is provided, ensure the normalized path is within base
        if base:
            base_normalized = str(Path(base).as_posix())
            # Ensure base ends with separator for proper prefix matching
            if not base_normalized.endswith("/"):
                base_normalized += "/"

            # Allow exact match (normalized equals base) or prefix match (inside base)
            if normalized != base_normalized and not normalized.startswith(base_normalized):
                raise PathTraversalError(
                    f"Path traversal detected: '{path}' escapes base directory '{base}'"
                )

        return normalized

    @staticmethod
    def validate_no_traversal(path: str) -> bool:
        """Check for path traversal attempts.

        Args:
            path: The path to validate.

        Returns:
            True if safe.

        Raises:
            PathTraversalError: If dangerous patterns are detected.
        """
        # Check for direct traversal patterns
        for pattern in PathNormalizer.TRAVERSAL_PATTERNS:
            if pattern in path:
                # Make sure it's actually a path component, not just a substring
                path_parts = path.replace("\\", "/").split("/")
                if pattern in path_parts:
                    raise PathTraversalError(
                        f"Path traversal detected: '{pattern}' in path '{path}'"
                    )

        # Also check for encoded traversal
        path_lower = path.lower()
        if "%2e%2e" in path_lower or "%252e" in path_lower:
            raise PathTraversalError(f"URL-encoded path traversal detected in '{path}'")

        return True

    @staticmethod
    def is_safe_relative(path: str, base: str) -> bool:
        """Verify path stays within base directory.

        Args:
            path: The path to check.
            base: The base directory.

        Returns:
            True if path is safely within base.
        """
        try:
            normalized = PathNormalizer.normalize(path, base)
            base_normalized = str(Path(base).as_posix())

            # Ensure base ends with separator
            if not base_normalized.endswith("/"):
                base_normalized += "/"

            return normalized.startswith(base_normalized)
        except PathTraversalError:
            return False

    @staticmethod
    def validate_symlinks(path: str, base: str) -> bool:
        """Validate that a path doesn't escape via symlinks.

        Note: This is a best-effort check. On systems where we can't
        resolve symlinks, we'll do the best we can with path comparison.

        Args:
            path: The path to validate.
            base: The base directory that should contain the path.

        Returns:
            True if path doesn't escape via symlinks.

        Raises:
            PathTraversalError: If symlink escape is detected.
        """
        try:
            # Try to resolve the path
            path_obj = Path(path)
            base_obj = Path(base)

            # Try to resolve both to absolute paths
            try:
                resolved_path = path_obj.resolve()
                resolved_base = base_obj.resolve()

                # Check if resolved path is under resolved base
                try:
                    resolved_path.relative_to(resolved_base)
                    return True
                except ValueError as e:
                    raise PathTraversalError(
                        f"Path '{path}' escapes base directory '{base}' via symlink"
                    ) from e
            except (OSError, RuntimeError):
                # Can't resolve symlinks, fall back to basic check
                # This is less secure but the best we can do in some environments
                logger.warning(
                    "symlink_resolution_skipped",
                    path=path,
                    base=base,
                    reason="cannot_resolve_symlinks",
                )
                return PathNormalizer.is_safe_relative(path, base)

        except PathTraversalError:
            raise
        except Exception as e:
            logger.warning(
                "symlink_validation_error",
                path=path,
                base=base,
                error=str(e),
            )
            # Fail closed - if we can't validate, reject
            raise PathTraversalError(f"Could not validate symlink safety for '{path}'") from e

    @staticmethod
    def validate_absolute(path: str, require_absolute: bool = True) -> bool:
        """Validate path is absolute or convert to absolute.

        Args:
            path: The path to validate.
            require_absolute: If True, path must be absolute. If False,
                convert to absolute based on current directory.

        Returns:
            True if path is valid.

        Raises:
            PathTraversalError: If path format is invalid.
        """
        if not path:
            raise PathTraversalError("Path cannot be empty")

        path_obj = Path(path)

        if require_absolute and not path_obj.is_absolute():
            raise PathTraversalError(f"Path must be absolute: '{path}'")

        return True

    @staticmethod
    def validate_extension(extension: str, allowed_extensions: list[str]) -> bool:
        """Validate file extension against allowlist.

        Args:
            extension: File extension to validate (with or without leading dot).
            allowed_extensions: List of allowed extensions.

        Returns:
            True if extension is allowed.

        Raises:
            PathTraversalError: If extension is not allowed.
        """
        # Ensure extension starts with dot
        if extension and not extension.startswith("."):
            extension = "." + extension

        if extension and extension not in allowed_extensions:
            raise PathTraversalError(
                f"Extension '{extension}' not in allowed list: {allowed_extensions}"
            )

        return True

    @staticmethod
    def build_safe_path(base: str, *parts: str) -> str:
        """Build a safe path by joining base with parts.

        This is a convenience method for constructing safe paths
        when you need to combine a base directory with relative parts.

        Args:
            base: Base directory.
            *parts: Path parts to append.

        Returns:
            Combined normalized path.

        Raises:
            PathTraversalError: If resulting path escapes base.
        """
        combined = str(Path(base).joinpath(*parts).as_posix())
        return PathNormalizer.normalize(combined, base)

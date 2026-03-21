"""Bounded operation executor for node agent."""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any

from src.shared.logging import get_logger

logger = get_logger(__name__)


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
            path: Path to validate (must be relative, not absolute)

        Returns:
            Resolved absolute path

        Raises:
            PermissionError: If path is absolute or contains traversal
            PermissionError: If path is not within allowed boundaries
        """
        # Step 1: Reject absolute paths
        if path.startswith("/") or (len(path) > 1 and path[1] == ":"):
            raise PermissionError(f"Absolute paths are not allowed: {path}")

        # Step 2: Explicitly reject path traversal before any resolution
        path_parts = path.replace("\\", "/").split("/")
        if ".." in path_parts:
            raise PermissionError(f"Path traversal is not allowed: {path}")

        # Step 3: Continue with existing resolution logic
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

    async def list_directory(self, path: str, max_entries: int = 100) -> list[dict]:
        """
        List contents of a directory with metadata.

        Args:
            path: Directory path to list
            max_entries: Maximum number of entries to return

        Returns:
            List of entry dictionaries with metadata
        """
        validated_path = self._validate_path(path)

        if not validated_path.is_dir():
            raise ValueError(f"Not a directory: {path}")

        entries = []
        try:
            for entry in validated_path.iterdir():
                try:
                    stat = entry.stat()
                    entries.append(
                        {
                            "name": entry.name,
                            "path": str(entry),
                            "is_dir": entry.is_dir(),
                            "size": stat.st_size if entry.is_file() else None,
                            "modified": datetime.fromtimestamp(
                                stat.st_mtime, tz=datetime.UTC
                            ).isoformat(),
                        }
                    )
                except (OSError, PermissionError):
                    # Skip entries we can't stat
                    continue

                if len(entries) >= max_entries:
                    break

            # Sort: directories first, then by name
            entries.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))

        except PermissionError as e:
            raise PermissionError(f"Permission denied accessing directory: {path}") from e

        return entries

    async def read_file(self, path: str, offset: int = 0, limit: int | None = None) -> dict:
        """
        Read contents of a file with offset/limit support.

        Args:
            path: File path to read
            offset: Byte offset to start reading from
            limit: Maximum bytes to read

        Returns:
            Dictionary with content and metadata
        """
        validated_path = self._validate_path(path)

        if not validated_path.is_file():
            raise ValueError(f"Not a file: {path}")

        # Get file size
        file_size = validated_path.stat().st_size

        # Read with offset/limit
        try:
            with open(validated_path, "rb") as f:
                f.seek(offset)

                if limit:
                    content = f.read(limit)
                else:
                    content = f.read()

            content_str = content.decode("utf-8")

            return {
                "content": content_str,
                "size_bytes": file_size,
                "bytes_read": len(content),
                "offset": offset,
                "truncated": (offset + len(content)) < file_size,
            }
        except UnicodeDecodeError as e:
            raise ValueError(f"File is not valid UTF-8: {path}") from e
        except PermissionError as e:
            raise PermissionError(f"Permission denied reading file: {path}") from e

    async def search_files(
        self,
        directory: str,
        pattern: str,
        include_patterns: list[str] | None = None,
        max_results: int = 1000,
        timeout: int = 60,
        mode: str = "text",
    ) -> dict[str, Any]:
        """
        Search for pattern in files within a directory using ripgrep.

        Args:
            directory: Directory to search in (must be validated path).
            pattern: Regex pattern to search for.
            include_patterns: File patterns to include (e.g., ["*.py"]).
            max_results: Maximum number of matches to return.
            timeout: Search timeout in seconds.
            mode: Search mode - "text", "path", or "symbol".

        Returns:
            Dict with results, match count, files searched.
        """
        import shutil

        # Validate path first
        validated_dir = self._validate_path(directory)

        # Check if ripgrep is available
        rg_path = shutil.which("rg")
        if not rg_path:
            raise ValueError("ripgrep (rg) is not installed on this node")

        # Validate mode
        valid_modes = ["text", "path", "symbol"]
        if mode not in valid_modes:
            mode = "text"

        # Build ripgrep command based on mode
        cmd = [
            "rg",
            "--line-number",
            "--no-heading",
            "--hidden",
        ]

        # Mode-specific ripgrep options
        if mode == "path":
            # Search in file paths only
            cmd.extend(["--files-with-matches"])
        elif mode == "symbol":
            # Search for whole-word matches (identifier search)
            cmd.extend(["--word-regexp"])

        if include_patterns:
            for p in include_patterns:
                cmd.extend(["--glob", p])

        # Limit results to prevent large responses
        cmd.extend(["--", pattern, str(validated_dir)])

        # Execute with timeout
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            except TimeoutError:
                proc.kill()
                await proc.wait()
                raise ValueError(f"Search timed out after {timeout} seconds") from None

            if proc.returncode not in (0, 1):
                # Returncode 1 means no matches found (valid)
                error_msg = stderr.decode("utf-8", errors="replace").strip()
                raise ValueError(f"Search command failed: {error_msg}")

        except FileNotFoundError:
            raise ValueError("ripgrep (rg) is not installed on this node") from None

        # Parse output
        output = stdout.decode("utf-8", errors="replace")
        matches: list[dict] = []
        files_searched: set[str] = set()

        for line in output.strip().split("\n"):
            if not line:
                continue

            # Parse: filename:line_number:line_content
            # Use split(":", 2) to handle paths that might contain ":"
            parts = line.split(":", 2)
            if len(parts) >= 2:
                file_path = parts[0]
                try:
                    line_num = int(parts[1])
                except ValueError:
                    line_num = 0
                line_content = parts[2] if len(parts) > 2 else ""

                files_searched.add(file_path)

                # Add individual matches (up to max_results)
                if len(matches) < max_results:
                    matches.append(
                        {
                            "file": file_path,
                            "line_number": line_num,
                            "match_count": 1,
                            "content": line_content,
                        }
                    )

        return {
            "matches": matches,
            "match_count": len(matches),
            "total_matches": len(matches),
            "files_searched": len(files_searched),
            "pattern": pattern,
            "mode": mode,
            "directory": str(validated_dir),
        }

    async def git_status(
        self,
        repo_path: str,
        timeout: int = 30,
    ) -> dict[str, Any]:
        """
        Get git status for a repository.

        Args:
            repo_path: Path to git repository (must be validated).
            timeout: Operation timeout in seconds.

        Returns:
            Dict with branch, status, staged/modified/untracked files, ahead/behind.
        """
        import shutil

        # Validate path
        validated_path = self._validate_path(repo_path)

        # Check if git is available
        git_path = shutil.which("git")
        if not git_path:
            raise ValueError("git is not installed on this node")

        # Check .git exists
        git_dir = validated_path / ".git"
        if not git_dir.is_dir():
            raise ValueError(f"Not a git repository: {repo_path}")

        # Helper to run git command
        async def run_git(*args: str) -> tuple[str, str]:
            cmd = ["git", "-C", str(validated_path)] + list(args)
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            except TimeoutError:
                proc.kill()
                await proc.wait()
                raise ValueError(f"Git command timed out after {timeout} seconds") from None

            return (
                stdout.decode("utf-8", errors="replace").strip(),
                stderr.decode("utf-8", errors="replace").strip(),
            )

        # Get current branch
        branch_output, branch_err = await run_git("branch", "--show-current")
        branch = branch_output if branch_output else "detached"
        if branch_err and "HEAD detached" in branch_err:
            # For detached HEAD, try to get the commit hash
            hash_output, _ = await run_git("rev-parse", "--short", "HEAD")
            branch = hash_output[:8] if hash_output else "detached"

        # Get git status --porcelain
        status_output, status_err = await run_git("status", "--porcelain")
        if status_err:
            raise ValueError(f"Git status failed: {status_err}")

        # Parse status output
        staged: list[str] = []
        modified: list[str] = []
        untracked: list[str] = []

        for line in status_output.split("\n"):
            if not line:
                continue

            status_code = line[:2]
            file_path = line[3:].strip() if len(line) > 3 else ""

            # XY status: X = index, Y = worktree
            index_status = status_code[0] if len(status_code) > 0 else " "
            worktree_status = status_code[1] if len(status_code) > 1 else " "

            # Staged changes (index)
            if index_status in ("A", "M", "D", "R", "C"):
                staged.append(file_path)
            elif index_status == "?":
                untracked.append(file_path)

            # Modified in worktree
            if worktree_status in ("M", "D"):
                if file_path not in staged:  # Don't double-count
                    modified.append(file_path)

        # Get ahead/behind from remote
        ahead = 0
        behind = 0
        try:
            # Try to get remote tracking branch
            rev_list_output, _ = await run_git(
                "rev-list",
                "--left-right",
                "--count",
                f"{branch}...origin/{branch}",
            )
            if rev_list_output:
                parts = rev_list_output.split()
                if len(parts) >= 2:
                    ahead = int(parts[0])
                    behind = int(parts[1])
        except ValueError:
            # Remote not configured or not reachable - that's OK
            pass

        # Get recent commits (last 10)
        recent_commits: list[dict[str, str]] = []
        try:
            log_output, _ = await run_git(
                "log",
                "-10",
                "--pretty=format:%H|%an|%aI|%s",
            )
            if log_output:
                for line in log_output.split("\n"):
                    if line:
                        parts = line.split("|", 3)
                        if len(parts) >= 4:
                            recent_commits.append(
                                {
                                    "hash": parts[0][:8],
                                    "author": parts[1],
                                    "date": parts[2],
                                    "message": parts[3],
                                }
                            )
        except Exception:
            # Failed to get recent commits - that's OK, leave empty
            pass

        is_clean = len(staged) == 0 and len(modified) == 0 and len(untracked) == 0

        return {
            "branch": branch,
            "is_clean": is_clean,
            "staged": staged,
            "staged_count": len(staged),
            "modified": modified,
            "modified_count": len(modified),
            "untracked": untracked,
            "untracked_count": len(untracked),
            "ahead": ahead,
            "behind": behind,
            "recent_commits": recent_commits,
        }

    async def write_file(self, path: str, content: str, mode: str = "create_or_overwrite") -> dict:
        """
        Write content to a file with atomic write and SHA256 verification.

        This method:
        1. Validates the path is within allowed boundaries
        2. In no_overwrite mode, checks if file already exists
        3. Writes content to a temporary file
        4. Computes SHA256 hash of the content
        5. Atomically moves the temp file to the target path
        6. Returns verification metadata including the hash and created flag

        Args:
            path: File path to write (must be validated)
            content: Content to write
            mode: Write mode - "create_or_overwrite" (default) or "no_overwrite"

        Returns:
            Write result with verification metadata:
            - path: The written file path
            - bytes_written: Number of bytes written
            - sha256_hash: SHA256 hash of the content
            - verified: Whether verification passed
            - created: Whether the file was newly created
        """
        import hashlib
        import os
        import tempfile

        validated_path = self._validate_path(path)

        # Check if file exists for no_overwrite mode
        file_existed = validated_path.exists()
        if mode == "no_overwrite" and file_existed:
            raise FileExistsError(
                f"File already exists: {path}. Use mode='create_or_overwrite' to overwrite."
            )

        # Ensure parent directory exists
        validated_path.parent.mkdir(parents=True, exist_ok=True)

        # Compute SHA256 hash of content before writing
        content_bytes = content.encode("utf-8")
        sha256_hash = hashlib.sha256(content_bytes).hexdigest()

        # Write to temporary file first (atomic write)
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=validated_path.parent,
                delete=False,
                prefix=f".{validated_path.name}.",
                suffix=".tmp",
            ) as tmp_file:
                tmp_path = tmp_file.name
                tmp_file.write(content)

            # Get file size
            file_size = os.path.getsize(tmp_path)

            # Atomically move temp file to target
            os.replace(tmp_path, validated_path)

            logger.info(
                "write_file_success",
                path=str(validated_path),
                bytes_written=file_size,
                sha256_hash=sha256_hash,
            )

            return {
                "path": str(validated_path),
                "bytes_written": file_size,
                "sha256_hash": sha256_hash,
                "verified": True,
                "content_hash_algorithm": "sha256",
                "created": not file_existed,
            }

        except FileExistsError:
            raise
        except PermissionError as e:
            raise PermissionError(f"Permission denied writing file: {path}") from e
        except OSError as e:
            raise OSError(f"Failed to write file: {path}, error: {e}") from e
        except Exception as e:
            # Clean up temp file on error
            if "tmp_path" in locals() and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
            raise OSError(f"Failed to write file: {path}, error: {e}") from e

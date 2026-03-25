"""Tests for node agent executor."""

import os
import tempfile
from pathlib import Path

import pytest

from src.node_agent.executor import OperationExecutor


# =============================================================================
# Happy-path tests
# =============================================================================


def test_executor_init_with_allowed_paths():
    """Test initializing executor with allowed paths."""
    executor = OperationExecutor(allowed_paths=["/tmp", "/home"])
    assert len(executor.allowed_paths) == 2


def test_executor_validate_path_within_allowed():
    """Test allowing path inside boundary."""
    with tempfile.TemporaryDirectory() as tmpdir:
        executor = OperationExecutor(allowed_paths=[tmpdir])
        validated = executor._validate_path(tmpdir + "/subdir/file.txt")
        assert str(validated).startswith(tmpdir)


@pytest.mark.asyncio
async def test_executor_list_directory():
    """Test listing directory contents with metadata."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        Path(tmpdir, "file1.txt").write_text("content1")
        Path(tmpdir, "file2.py").write_text("content2")
        os.makedirs(Path(tmpdir, "subdir").as_posix())

        executor = OperationExecutor(allowed_paths=[tmpdir])
        entries = await executor.list_directory(tmpdir)

        assert len(entries) == 3
        names = [e["name"] for e in entries]
        assert "file1.txt" in names
        assert "file2.py" in names
        assert "subdir" in names

        # Verify metadata
        file1_entry = next(e for e in entries if e["name"] == "file1.txt")
        assert file1_entry["is_dir"] is False
        assert file1_entry["size"] is not None


@pytest.mark.asyncio
async def test_executor_list_directory_max_entries():
    """Test respects max_entries limit."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create more than 2 files
        for i in range(5):
            Path(tmpdir, f"file{i}.txt").write_text(f"content{i}")

        executor = OperationExecutor(allowed_paths=[tmpdir])
        entries = await executor.list_directory(tmpdir, max_entries=2)

        assert len(entries) == 2


@pytest.mark.asyncio
async def test_executor_read_file():
    """Test reading file with offset/limit."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir, "test.txt")
        test_file.write_text("Hello, World!")

        executor = OperationExecutor(allowed_paths=[tmpdir])

        # Read full file
        result = await executor.read_file(str(test_file))
        assert result["content"] == "Hello, World!"
        assert result["size_bytes"] == 13
        assert result["truncated"] is False

        # Read with limit
        result = await executor.read_file(str(test_file), limit=5)
        assert result["content"] == "Hello"
        assert result["bytes_read"] == 5

        # Read with offset
        result = await executor.read_file(str(test_file), offset=7)
        assert result["content"] == "World!"


@pytest.mark.asyncio
async def test_executor_read_file_truncation():
    """Test truncated flag is set correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir, "test.txt")
        test_file.write_text("Short content")

        executor = OperationExecutor(allowed_paths=[tmpdir])
        result = await executor.read_file(str(test_file))

        # Full read should not be truncated
        assert result["truncated"] is False

        # Partial read should be truncated
        result = await executor.read_file(str(test_file), limit=5)
        assert result["truncated"] is True


@pytest.mark.asyncio
async def test_executor_search_files_text_mode():
    """Test search in text mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir, "test.py")
        test_file.write_text("def hello():\n    print('hello')")

        executor = OperationExecutor(allowed_paths=[tmpdir])
        result = await executor.search_files(tmpdir, "hello", mode="text")

        assert result["match_count"] > 0
        assert result["mode"] == "text"


@pytest.mark.asyncio
async def test_executor_search_files_path_mode():
    """Test search in path mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create files with matching names
        Path(tmpdir, "test_hello.py").write_text("pass")
        Path(tmpdir, "other.py").write_text("pass")

        executor = OperationExecutor(allowed_paths=[tmpdir])
        result = await executor.search_files(tmpdir, "hello", mode="path")

        assert result["mode"] == "path"
        # Path mode returns files with matches


@pytest.mark.asyncio
async def test_executor_search_files_symbol_mode():
    """Test search in symbol mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir, "test.py")
        test_file.write_text("class MyClass:\n    pass")

        executor = OperationExecutor(allowed_paths=[tmpdir])
        result = await executor.search_files(tmpdir, "MyClass", mode="symbol")

        assert result["mode"] == "symbol"


@pytest.mark.asyncio
async def test_executor_search_files_no_matches():
    """Test handling no matches gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir, "test.py")
        test_file.write_text("print('hello')")

        executor = OperationExecutor(allowed_paths=[tmpdir])
        result = await executor.search_files(tmpdir, "nonexistent_pattern")

        assert result["match_count"] == 0
        assert result["matches"] == []


@pytest.mark.asyncio
async def test_executor_git_status():
    """Test getting git status with all fields."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Initialize git repo
        os.system(f"cd {tmpdir} && git init -q")
        Path(tmpdir, "README.md").write_text("# Test")

        executor = OperationExecutor(allowed_paths=[tmpdir])
        result = await executor.git_status(tmpdir)

        assert "branch" in result
        assert "is_clean" in result
        assert "staged" in result
        assert "modified" in result
        assert "untracked" in result
        assert "ahead" in result
        assert "behind" in result


@pytest.mark.asyncio
async def test_executor_git_status_recent_commits():
    """Test verifying recent_commits field in git status."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Initialize git repo and make a commit
        os.system(f"cd {tmpdir} && git init -q")
        Path(tmpdir, "file.txt").write_text("content")
        os.system(f"cd {tmpdir} && git add . && git commit -q -m 'Initial commit'")

        executor = OperationExecutor(allowed_paths=[tmpdir])
        result = await executor.git_status(tmpdir)

        assert "recent_commits" in result
        # Should have at least one commit
        assert len(result["recent_commits"]) >= 1
        commit = result["recent_commits"][0]
        assert "hash" in commit
        assert "author" in commit
        assert "date" in commit
        assert "message" in commit


@pytest.mark.asyncio
async def test_executor_write_file_create():
    """Test creating a new file with atomic write."""
    with tempfile.TemporaryDirectory() as tmpdir:
        executor = OperationExecutor(allowed_paths=[tmpdir])
        file_path = str(Path(tmpdir, "new_file.txt"))

        result = await executor.write_file(file_path, "Hello, World!")

        assert result["bytes_written"] > 0
        assert result["sha256_hash"] is not None
        assert result["verified"] is True
        assert result["created"] is True

        # Verify file content
        assert Path(file_path).read_text() == "Hello, World!"


@pytest.mark.asyncio
async def test_executor_write_file_overwrite():
    """Test overwriting an existing file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir, "existing.txt")
        test_file.write_text("Original content")

        executor = OperationExecutor(allowed_paths=[tmpdir])
        result = await executor.write_file(
            str(test_file), "New content", mode="create_or_overwrite"
        )

        assert result["created"] is False
        assert test_file.read_text() == "New content"


@pytest.mark.asyncio
async def test_executor_write_file_verification():
    """Test SHA256 verification in response."""
    with tempfile.TemporaryDirectory() as tmpdir:
        executor = OperationExecutor(allowed_paths=[tmpdir])
        file_path = str(Path(tmpdir, "verify.txt"))

        result = await executor.write_file(file_path, "Test content for verification")

        assert "sha256_hash" in result
        assert "content_hash_algorithm" in result
        assert result["content_hash_algorithm"] == "sha256"
        assert result["verified"] is True


# =============================================================================
# Error-path tests
# =============================================================================


def test_executor_validate_path_outside_allowed():
    """Test rejecting path outside allowed boundary."""
    executor = OperationExecutor(allowed_paths=["/tmp"])

    with pytest.raises(PermissionError, match="Path is outside allowed directories"):
        executor._validate_path("/etc/passwd")


def test_executor_validate_path_no_allowed():
    """Test denying all when no paths configured."""
    executor = OperationExecutor(allowed_paths=None)

    with pytest.raises(PermissionError, match="No allowed paths"):
        executor._validate_path("/tmp/anywhere")


def test_executor_validate_path_traversal():
    """Test rejecting path traversal attempts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        executor = OperationExecutor(allowed_paths=[tmpdir])

        # Try path traversal
        with pytest.raises(PermissionError):
            executor._validate_path(f"{tmpdir}/../etc/passwd")


@pytest.mark.asyncio
async def test_executor_list_directory_not_dir():
    """Test raising ValueError for non-directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir, "file.txt")
        test_file.write_text("content")

        executor = OperationExecutor(allowed_paths=[tmpdir])

        with pytest.raises(ValueError, match="Not a directory"):
            await executor.list_directory(str(test_file))


@pytest.mark.asyncio
async def test_executor_read_file_not_file():
    """Test raising ValueError for non-file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir, "subdir")
        test_dir.mkdir()

        executor = OperationExecutor(allowed_paths=[tmpdir])

        with pytest.raises(ValueError, match="Not a file"):
            await executor.read_file(str(test_dir))


@pytest.mark.asyncio
async def test_executor_read_file_not_utf8():
    """Test raising ValueError for binary files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir, "binary.bin")
        # Write binary content (not valid UTF-8)
        test_file.write_bytes(b"\x00\x01\x02\xff\xfe")

        executor = OperationExecutor(allowed_paths=[tmpdir])

        with pytest.raises(ValueError, match="not valid UTF-8"):
            await executor.read_file(str(test_file))


@pytest.mark.asyncio
async def test_executor_write_file_no_overwrite():
    """Test raising FileExistsError in no_overwrite mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir, "existing.txt")
        test_file.write_text("existing content")

        executor = OperationExecutor(allowed_paths=[tmpdir])

        with pytest.raises(FileExistsError, match="already exists"):
            await executor.write_file(str(test_file), "new content", mode="no_overwrite")

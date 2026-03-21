"""Operation handlers for node agent.

These endpoints provide bounded file operations:
- list_directory: Lists directory contents with metadata
- read_file: Reads file contents with offset/limit support
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.node_agent.dependencies import get_executor
from src.node_agent.executor import OperationExecutor
from src.shared.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


class OperationRequest(BaseModel):
    """Base operation request."""

    path: str


class ListDirRequest(OperationRequest):
    """Request to list directory contents."""

    max_entries: int = 100


class ReadFileRequest(OperationRequest):
    """Request to read a file."""

    offset: int = 0
    limit: int | None = None


class SearchRequest(BaseModel):
    """Request to search in files."""

    directory: str
    pattern: str
    include_patterns: list[str] | None = None
    max_results: int = 1000
    timeout: int = 60


class GitStatusRequest(BaseModel):
    """Request to get git status."""

    path: str
    timeout: int = 30


class WriteFileRequest(BaseModel):
    """Request to write a file."""

    path: str
    content: str
    mode: str = "create_or_overwrite"


class OperationResponse(BaseModel):
    """Base operation response."""

    success: bool
    message: str
    data: dict | list | str | None = None


@router.post("/operations/list-dir", response_model=OperationResponse)
async def list_dir(
    request: ListDirRequest,
    executor: OperationExecutor = Depends(get_executor),
) -> OperationResponse:
    """List directory contents with metadata.

    Returns file and directory entries including:
    - name: Entry name
    - path: Full path
    - is_dir: Whether entry is a directory
    - size: File size in bytes (None for directories)
    - modified: Last modified timestamp (ISO format)
    """
    try:
        # Validate max_entries
        max_entries = request.max_entries
        if max_entries < 1:
            max_entries = 1
        elif max_entries > 500:
            max_entries = 500

        entries = await executor.list_directory(request.path, max_entries)

        logger.info(
            "list_dir_success",
            path=request.path,
            entry_count=len(entries),
        )

        return OperationResponse(
            success=True,
            message=f"Listed {len(entries)} entries",
            data={
                "entries": entries,
                "total": len(entries),
                "path": request.path,
            },
        )
    except PermissionError as e:
        logger.warning("list_dir_permission_denied", path=request.path, error=str(e))
        return OperationResponse(
            success=False,
            message=str(e),
            data=None,
        )
    except ValueError as e:
        logger.warning("list_dir_invalid_path", path=request.path, error=str(e))
        return OperationResponse(
            success=False,
            message=str(e),
            data=None,
        )
    except Exception as e:
        logger.error("list_dir_error", path=request.path, error=str(e))
        return OperationResponse(
            success=False,
            message=str(e),
            data=None,
        )


@router.post("/operations/read-file", response_model=OperationResponse)
async def read_file(
    request: ReadFileRequest,
    executor: OperationExecutor = Depends(get_executor),
) -> OperationResponse:
    """Read file contents with offset and limit support.

    Returns:
    - content: File content as string
    - size_bytes: Total file size
    - bytes_read: Number of bytes actually read
    - offset: Starting offset
    - truncated: Whether there's more content
    """
    try:
        # Validate offset
        offset = request.offset
        if offset < 0:
            offset = 0

        result = await executor.read_file(request.path, offset, request.limit)

        logger.info(
            "read_file_success",
            path=request.path,
            bytes_read=result["bytes_read"],
            offset=offset,
        )

        return OperationResponse(
            success=True,
            message=f"Read {result['bytes_read']} bytes",
            data=result,
        )
    except PermissionError as e:
        logger.warning("read_file_permission_denied", path=request.path, error=str(e))
        return OperationResponse(
            success=False,
            message=str(e),
            data=None,
        )
    except ValueError as e:
        logger.warning("read_file_invalid_path", path=request.path, error=str(e))
        return OperationResponse(
            success=False,
            message=str(e),
            data=None,
        )
    except Exception as e:
        logger.error("read_file_error", path=request.path, error=str(e))
        return OperationResponse(
            success=False,
            message=str(e),
            data=None,
        )


@router.post("/operations/search", response_model=OperationResponse)
async def search(
    request: SearchRequest,
    executor: OperationExecutor = Depends(get_executor),
) -> OperationResponse:
    """Search for pattern in files.

    Uses ripgrep for efficient text search with file pattern filtering.
    Returns structured results with file, line number, and match content.
    """
    try:
        # Validate inputs
        max_results = request.max_results
        if max_results < 1:
            max_results = 1
        elif max_results > 1000:
            max_results = 1000

        timeout = request.timeout
        if timeout < 1:
            timeout = 1
        elif timeout > 120:
            timeout = 120

        # Validate mode
        valid_modes = ["text", "path", "symbol"]
        mode = request.mode if request.mode in valid_modes else "text"

        result = await executor.search_files(
            directory=request.directory,
            pattern=request.pattern,
            include_patterns=request.include_patterns,
            max_results=max_results,
            timeout=timeout,
            mode=mode,
        )

        match_count = result.get("match_count", 0)

        logger.info(
            "search_success",
            directory=request.directory,
            pattern=request.pattern,
            mode=mode,
            match_count=match_count,
            files_searched=result.get("files_searched", 0),
        )

        return OperationResponse(
            success=True,
            message=f"Found {match_count} matches",
            data=result,
        )
    except PermissionError as e:
        logger.warning("search_permission_denied", directory=request.directory, error=str(e))
        return OperationResponse(
            success=False,
            message=str(e),
            data=None,
        )
    except ValueError as e:
        logger.warning("search_invalid_params", directory=request.directory, error=str(e))
        return OperationResponse(
            success=False,
            message=str(e),
            data=None,
        )
    except Exception as e:
        logger.error("search_error", directory=request.directory, error=str(e))
        return OperationResponse(
            success=False,
            message=str(e),
            data=None,
        )


@router.post("/operations/git-status", response_model=OperationResponse)
async def git_status(
    request: GitStatusRequest,
    executor: OperationExecutor = Depends(get_executor),
) -> OperationResponse:
    """Get git status for a repository.

    Returns branch, clean/dirty status, staged/modified/untracked files,
    and ahead/behind count relative to remote.
    """
    try:
        # Validate timeout
        timeout = request.timeout
        if timeout < 1:
            timeout = 1
        elif timeout > 60:
            timeout = 60

        result = await executor.git_status(
            repo_path=request.path,
            timeout=timeout,
        )

        logger.info(
            "git_status_success",
            path=request.path,
            branch=result.get("branch", "unknown"),
            is_clean=result.get("is_clean", False),
        )

        return OperationResponse(
            success=True,
            message="Git status retrieved",
            data=result,
        )
    except PermissionError as e:
        logger.warning("git_status_permission_denied", path=request.path, error=str(e))
        return OperationResponse(
            success=False,
            message=str(e),
            data=None,
        )
    except ValueError as e:
        logger.warning("git_status_invalid_params", path=request.path, error=str(e))
        return OperationResponse(
            success=False,
            message=str(e),
            data=None,
        )
    except Exception as e:
        logger.error("git_status_error", path=request.path, error=str(e))
        return OperationResponse(
            success=False,
            message=str(e),
            data=None,
        )


@router.post("/operations/write-file", response_model=OperationResponse)
async def write_file(
    request: WriteFileRequest,
    executor: OperationExecutor = Depends(get_executor),
) -> OperationResponse:
    """Write content to a file with atomic write and verification.

    This endpoint:
    1. Validates the path is within allowed boundaries
    2. Writes content to a temporary file
    3. Computes SHA256 hash of the content
    4. Atomically moves the temp file to the target path
    5. Returns verification metadata including the hash

    Returns:
    - path: The written file path
    - bytes_written: Number of bytes written
    - sha256_hash: SHA256 hash of the content
    - verified: Whether verification passed
    """
    try:
        result = await executor.write_file(request.path, request.content, request.mode)

        logger.info(
            "write_file_success",
            path=request.path,
            bytes_written=result.get("bytes_written", 0),
            sha256_hash=result.get("sha256_hash", ""),
            created=result.get("created", False),
        )

        return OperationResponse(
            success=True,
            message=f"Wrote {result.get('bytes_written', 0)} bytes with SHA256 verification",
            data=result,
        )
    except FileExistsError as e:
        logger.warning("write_file_already_exists", path=request.path, error=str(e))
        return OperationResponse(
            success=False,
            message=str(e),
            data=None,
        )
    except PermissionError as e:
        logger.warning("write_file_permission_denied", path=request.path, error=str(e))
        return OperationResponse(
            success=False,
            message=str(e),
            data=None,
        )
    except ValueError as e:
        logger.warning("write_file_invalid_path", path=request.path, error=str(e))
        return OperationResponse(
            success=False,
            message=str(e),
            data=None,
        )
    except OSError as e:
        logger.error("write_file_error", path=request.path, error=str(e))
        return OperationResponse(
            success=False,
            message=str(e),
            data=None,
        )
    except Exception as e:
        logger.error("write_file_error", path=request.path, error=str(e))
        return OperationResponse(
            success=False,
            message=str(e),
            data=None,
        )

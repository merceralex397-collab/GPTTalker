"""Operation handlers for node agent.

These are placeholder routes that return 501 Not Implemented.
Actual implementations will be added in later tickets:
- REPO-002: list_directory, read_file
- REPO-003: search_files, git_status
- WRITE-001: write_file
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.shared.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


class OperationRequest(BaseModel):
    """Base operation request."""

    path: str


class ListDirRequest(OperationRequest):
    """Request to list directory contents."""

    pass


class ReadFileRequest(OperationRequest):
    """Request to read a file."""

    offset: int = 0
    limit: int | None = None


class SearchRequest(BaseModel):
    """Request to search in files."""

    directory: str
    pattern: str
    include_patterns: list[str] | None = None


class GitStatusRequest(OperationRequest):
    """Request to get git status."""

    pass


class WriteFileRequest(BaseModel):
    """Request to write a file."""

    path: str
    content: str


class OperationResponse(BaseModel):
    """Base operation response."""

    success: bool
    message: str
    data: dict | list | str | None = None


@router.post("/operations/list-dir", response_model=OperationResponse)
async def list_dir(request: ListDirRequest) -> OperationResponse:
    """List directory contents.

    This endpoint is not yet implemented.
    Will be implemented in REPO-002.
    """
    logger.warning("list_dir_not_implemented", path=request.path)
    raise HTTPException(status_code=501, detail="list_dir not yet implemented - see REPO-002")


@router.post("/operations/read-file", response_model=OperationResponse)
async def read_file(request: ReadFileRequest) -> OperationResponse:
    """Read file contents.

    This endpoint is not yet implemented.
    Will be implemented in REPO-002.
    """
    logger.warning("read_file_not_implemented", path=request.path)
    raise HTTPException(status_code=501, detail="read_file not yet implemented - see REPO-002")


@router.post("/operations/search", response_model=OperationResponse)
async def search(request: SearchRequest) -> OperationResponse:
    """Search for pattern in files.

    This endpoint is not yet implemented.
    Will be implemented in REPO-003.
    """
    logger.warning("search_not_implemented", directory=request.directory, pattern=request.pattern)
    raise HTTPException(status_code=501, detail="search not yet implemented - see REPO-003")


@router.post("/operations/git-status", response_model=OperationResponse)
async def git_status(request: GitStatusRequest) -> OperationResponse:
    """Get git status for a repository.

    This endpoint is not yet implemented.
    Will be implemented in REPO-003.
    """
    logger.warning("git_status_not_implemented", repo_path=request.path)
    raise HTTPException(status_code=501, detail="git_status not yet implemented - see REPO-003")


@router.post("/operations/write-file", response_model=OperationResponse)
async def write_file(request: WriteFileRequest) -> OperationResponse:
    """Write content to a file.

    This endpoint is not yet implemented.
    Will be implemented in WRITE-001.
    """
    logger.warning("write_file_not_implemented", path=request.path)
    raise HTTPException(status_code=501, detail="write_file not yet implemented - see WRITE-001")

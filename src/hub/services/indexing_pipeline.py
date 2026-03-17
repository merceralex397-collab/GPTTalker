"""Repository indexing pipeline with content-hash tracking."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

from src.hub.services.embedding_client import EmbeddingServiceClient
from src.hub.services.node_client import HubNodeClient
from src.hub.services.qdrant_client import QdrantClientWrapper
from src.shared.logging import get_logger
from src.shared.models import (
    FileIndexPayload,
    LLMServiceInfo,
    NodeInfo,
    RepoInfo,
    compute_content_hash,
    generate_file_id,
)

logger = get_logger(__name__)


class IndexMode(StrEnum):
    """Indexing mode for repository content."""

    INCREMENTAL = "incremental"
    FULL = "full"


@dataclass
class IndexResult:
    """Result of an indexing operation."""

    success: bool
    repo_id: str
    indexed_count: int = 0
    skipped_count: int = 0
    deleted_count: int = 0
    error: str | None = None
    duration_ms: int = 0


@dataclass
class FileToIndex:
    """Represents a file ready for indexing."""

    relative_path: str
    absolute_path: str
    content: str
    size_bytes: int
    line_count: int
    extension: str
    language: str | None


class IndexingPipeline:
    """Pipeline for indexing repository content into Qdrant.

    This pipeline reads repository files, generates embeddings, and stores
    them in Qdrant with content-hash tracking for idempotent reindexing.
    """

    # Configuration
    BATCH_SIZE: int = 10
    MAX_FILE_SIZE: int = 1_000_000
    MAX_RETRIES: int = 3
    CONTENT_PREVIEW_LENGTH: int = 500

    # File extensions to index
    INDEXABLE_EXTENSIONS: set[str] = {
        ".py",
        ".js",
        ".ts",
        ".jsx",
        ".tsx",
        ".java",
        ".go",
        ".rs",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".cs",
        ".rb",
        ".php",
        ".swift",
        ".kt",
        ".scala",
        ".md",
        ".txt",
        ".yaml",
        ".yml",
        ".json",
        ".toml",
        ".xml",
        ".sql",
        ".sh",
        ".bash",
        ".zsh",
    }

    # Directories to exclude
    EXCLUDED_DIRS: set[str] = {
        "node_modules",
        "__pycache__",
        ".git",
        ".svn",
        "venv",
        ".venv",
        "env",
        ".virtualenv",
        "dist",
        "build",
        "target",
        ".next",
        ".nuxt",
        ".svelte",
        "coverage",
        ".pytest_cache",
    }

    # Language detection by extension
    LANGUAGE_MAP: dict[str, str] = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".tsx": "typescript",
        ".java": "java",
        ".go": "go",
        ".rs": "rust",
        ".c": "c",
        ".cpp": "cpp",
        ".h": "c",
        ".hpp": "cpp",
        ".cs": "csharp",
        ".rb": "ruby",
        ".php": "php",
        ".swift": "swift",
        ".kt": "kotlin",
        ".scala": "scala",
        ".md": "markdown",
        ".txt": "text",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".json": "json",
        ".toml": "toml",
        ".xml": "xml",
        ".sql": "sql",
        ".sh": "shell",
        ".bash": "shell",
        ".zsh": "shell",
    }

    def __init__(
        self,
        qdrant_client: QdrantClientWrapper,
        embedding_client: EmbeddingServiceClient,
        embedding_service: LLMServiceInfo,
    ):
        """Initialize the indexing pipeline.

        Args:
            qdrant_client: Qdrant client wrapper.
            embedding_client: Embedding service client.
            embedding_service: Embedding service configuration.
        """
        self._qdrant = qdrant_client
        self._embedding = embedding_client
        self._embedding_service = embedding_service

    async def index_repo(
        self,
        repo: RepoInfo,
        node_client: HubNodeClient,
        node_info: NodeInfo,
        mode: IndexMode = IndexMode.INCREMENTAL,
    ) -> IndexResult:
        """Index a repository into Qdrant.

        Args:
            repo: Repository to index.
            node_client: HubNodeClient for reading files.
            node_info: Node information for the repo host.
            mode: Indexing mode (incremental or full).

        Returns:
            IndexResult with operation statistics.
        """
        start = datetime.utcnow()
        indexed = 0
        skipped = 0
        deleted = 0

        try:
            # 1. Discover all files in the repo
            logger.info("index_repo_discovering", repo_id=repo.repo_id, path=repo.path)
            files = await self._discover_files(node_client, node_info, repo.path)

            if not files:
                logger.warning("index_repo_no_files", repo_id=repo.repo_id)
                return IndexResult(
                    success=True,
                    repo_id=repo.repo_id,
                    indexed_count=0,
                    skipped_count=0,
                    deleted_count=0,
                    duration_ms=0,
                )

            logger.info(
                "index_repo_files_discovered",
                repo_id=repo.repo_id,
                file_count=len(files),
            )

            # 2. Process files in batches
            current_file_ids: set[str] = set()
            for batch in self._batch_files(files, self.BATCH_SIZE):
                batch_results = await self._process_batch(batch, repo, node_client, node_info, mode)
                indexed += batch_results["indexed"]
                skipped += batch_results["skipped"]
                current_file_ids.update(batch_results["file_ids"])

            # 3. Cleanup deleted files (incremental mode only)
            if mode == IndexMode.INCREMENTAL:
                deleted = await self._cleanup_deleted(repo.repo_id, current_file_ids)

            duration = int((datetime.utcnow() - start).total_seconds() * 1000)

            logger.info(
                "index_repo_success",
                repo_id=repo.repo_id,
                indexed=indexed,
                skipped=skipped,
                deleted=deleted,
                duration_ms=duration,
            )

            return IndexResult(
                success=True,
                repo_id=repo.repo_id,
                indexed_count=indexed,
                skipped_count=skipped,
                deleted_count=deleted,
                duration_ms=duration,
            )

        except Exception as e:
            logger.error("index_repo_failed", repo_id=repo.repo_id, error=str(e))
            return IndexResult(
                success=False,
                repo_id=repo.repo_id,
                error=str(e),
            )

    async def _discover_files(
        self,
        node_client: HubNodeClient,
        node_info: NodeInfo,
        root_path: str,
    ) -> list[FileToIndex]:
        """Discover all indexable files in a repository.

        Args:
            node_client: HubNodeClient for file operations.
            node_info: Node information.
            root_path: Root path of the repository.

        Returns:
            List of FileToIndex objects.
        """
        files: list[FileToIndex] = []
        await self._discover_files_recursive(node_client, node_info, root_path, root_path, files)
        return files

    async def _discover_files_recursive(
        self,
        node_client: HubNodeClient,
        node_info: NodeInfo,
        root_path: str,
        current_path: str,
        files: list[FileToIndex],
    ) -> None:
        """Recursively discover files in directories.

        Args:
            node_client: HubNodeClient for file operations.
            node_info: Node information.
            root_path: Root path of the repository.
            current_path: Current directory being explored.
            files: List to append discovered files to.
        """
        try:
            result = await node_client.list_directory(node_info, current_path)

            if not result.get("success"):
                logger.warning(
                    "index_repo_list_dir_failed",
                    path=current_path,
                    error=result.get("error"),
                )
                return

            entries = result.get("entries", [])

            for entry in entries:
                entry_path = entry.get("path", "")
                is_dir = entry.get("is_dir", False)

                # Get relative path
                if entry_path.startswith(root_path):
                    relative_path = entry_path[len(root_path) :].lstrip("/")
                else:
                    relative_path = entry_path

                # Check for excluded directories
                if is_dir:
                    dir_name = entry.get("name", "")
                    if dir_name in self.EXCLUDED_DIRS or dir_name.startswith("."):
                        continue
                    await self._discover_files_recursive(
                        node_client, node_info, root_path, entry_path, files
                    )
                else:
                    # Check if file is indexable
                    ext = self._get_extension(relative_path)
                    if not ext or ext not in self.INDEXABLE_EXTENSIONS:
                        continue

                    # Skip hidden files except .gitignore, .env.example
                    filename = entry.get("name", "")
                    if filename.startswith(".") and filename not in [".gitignore", ".env.example"]:
                        continue

                    files.append(
                        FileToIndex(
                            relative_path=relative_path,
                            absolute_path=entry_path,
                            content="",  # Content loaded during processing
                            size_bytes=entry.get("size", 0),
                            line_count=0,
                            extension=ext,
                            language=self.LANGUAGE_MAP.get(ext),
                        )
                    )

        except Exception as e:
            logger.warning(
                "index_repo_discover_error",
                path=current_path,
                error=str(e),
            )

    def _batch_files(self, files: list[FileToIndex], batch_size: int) -> list[list[FileToIndex]]:
        """Split files into batches.

        Args:
            files: List of files to batch.
            batch_size: Size of each batch.

        Returns:
            List of file batches.
        """
        batches: list[list[FileToIndex]] = []
        for i in range(0, len(files), batch_size):
            batches.append(files[i : i + batch_size])
        return batches

    def _get_extension(self, path: str) -> str:
        """Get file extension from path.

        Args:
            path: File path.

        Returns:
            Extension with leading dot, or empty string.
        """
        import os

        _, ext = os.path.splitext(path)
        return ext.lower() if ext else ""

    async def _process_batch(
        self,
        files: list[FileToIndex],
        repo: RepoInfo,
        node_client: HubNodeClient,
        node_info: NodeInfo,
        mode: IndexMode,
    ) -> dict[str, Any]:
        """Process a batch of files.

        Args:
            files: List of files to process.
            repo: Repository being indexed.
            node_client: HubNodeClient for reading files.
            node_info: Node information.
            mode: Indexing mode.

        Returns:
            Dictionary with processing results.
        """
        indexed = 0
        skipped = 0
        file_ids: list[str] = []

        # Read file contents
        for file_to_index in files:
            try:
                result = await node_client.read_file(node_info, file_to_index.absolute_path)

                if not result.get("success"):
                    logger.warning(
                        "index_repo_read_failed",
                        path=file_to_index.relative_path,
                        error=result.get("error"),
                    )
                    continue

                content = result.get("content", "")
                file_to_index.content = content
                file_to_index.line_count = content.count("\n") + (1 if content else 0)

                # Skip files that are too large
                if len(content.encode("utf-8")) > self.MAX_FILE_SIZE:
                    logger.debug(
                        "index_repo_file_too_large",
                        path=file_to_index.relative_path,
                        size=len(content),
                    )
                    continue

            except Exception as e:
                logger.warning(
                    "index_repo_read_error",
                    path=file_to_index.relative_path,
                    error=str(e),
                )
                continue

        # Generate embeddings for files that need indexing
        files_to_embed: list[FileToIndex] = []
        for file_to_index in files:
            # Check if we need to index this file
            should_index = await self._should_index_file(file_to_index, repo, mode)

            if should_index:
                files_to_embed.append(file_to_index)
            else:
                skipped += 1

            # Always track file ID
            file_id = generate_file_id(repo.repo_id, file_to_index.relative_path)
            file_ids.append(file_id)

        # Generate embeddings and upsert
        if files_to_embed:
            texts = [f.content for f in files_to_embed]
            embed_result = await self._embedding.embed_batch(
                service=self._embedding_service,
                texts=texts,
                encoding_format="float",
            )

            if embed_result.get("success"):
                embeddings = embed_result.get("embeddings", [])

                for file_to_index, vector in zip(files_to_embed, embeddings, strict=True):
                    await self._upsert_file_vector(file_to_index, repo, node_info, vector)
                    indexed += 1
            else:
                logger.error(
                    "index_repo_embedding_failed",
                    repo_id=repo.repo_id,
                    error=embed_result.get("error"),
                )

        return {
            "indexed": indexed,
            "skipped": skipped,
            "file_ids": file_ids,
        }

    async def _should_index_file(
        self,
        file_to_index: FileToIndex,
        repo: RepoInfo,
        mode: IndexMode,
    ) -> bool:
        """Determine if a file should be indexed.

        Args:
            file_to_index: File to check.
            repo: Repository being indexed.
            mode: Indexing mode.

        Returns:
            True if file should be indexed.
        """
        file_id = generate_file_id(repo.repo_id, file_to_index.relative_path)

        # Full reindex always processes all files
        if mode == IndexMode.FULL:
            return True

        # For incremental mode, check content hash
        content_hash = compute_content_hash(file_to_index.content)

        try:
            existing_record = await self._qdrant.get_file(file_id)

            if existing_record is None:
                # New file, needs indexing
                return True

            # Check if content hash matches
            payload = existing_record.payload
            if payload and payload.get("content_hash") == content_hash:
                # Content unchanged, skip
                logger.debug(
                    "index_repo_file_unchanged",
                    file_id=file_id,
                    path=file_to_index.relative_path,
                )
                return False

            # Content changed, needs reindexing
            return True

        except Exception as e:
            logger.warning(
                "index_repo_hash_check_error",
                file_id=file_id,
                error=str(e),
            )
            # On error, default to indexing
            return True

    async def _upsert_file_vector(
        self,
        file_to_index: FileToIndex,
        repo: RepoInfo,
        node_info: NodeInfo,
        vector: list[float],
    ) -> None:
        """Upsert a file vector to Qdrant.

        Args:
            file_to_index: File to upsert.
            repo: Repository being indexed.
            node_info: Node information.
            vector: Embedding vector.
        """
        import traceback

        file_id = generate_file_id(repo.repo_id, file_to_index.relative_path)
        content_hash = compute_content_hash(file_to_index.content)

        # Truncate content for preview
        preview_length = min(len(file_to_index.content), self.CONTENT_PREVIEW_LENGTH)
        content_preview = file_to_index.content[:preview_length]

        payload = FileIndexPayload(
            file_id=file_id,
            repo_id=repo.repo_id,
            node_id=node_info.node_id,
            path=file_to_index.absolute_path,
            relative_path=file_to_index.relative_path,
            filename=file_to_index.relative_path.split("/")[-1],
            extension=file_to_index.extension,
            content_hash=content_hash,
            size_bytes=len(file_to_index.content.encode("utf-8")),
            line_count=file_to_index.line_count,
            language=file_to_index.language,
            indexed_at=datetime.utcnow(),
            indexed_by="index_repo",
            content_preview=content_preview,
            metadata={},
        )

        try:
            await self._qdrant.upsert_file(
                file_id=file_id,
                vector=vector,
                payload=payload,
            )
            logger.debug(
                "index_repo_file_indexed",
                file_id=file_id,
                path=file_to_index.relative_path,
            )
        except Exception:
            logger.error(
                "index_repo_file_upsert_failed",
                file_id=file_id,
                path=file_to_index.relative_path,
                error=traceback.format_exc(),
            )

    async def _cleanup_deleted(
        self,
        repo_id: str,
        current_file_ids: set[str],
    ) -> int:
        """Delete vectors for files that no longer exist in the repo.

        Args:
            repo_id: Repository ID.
            current_file_ids: Set of file IDs currently in the repo.

        Returns:
            Number of deleted files.
        """
        try:
            # Get all existing file IDs for this repo
            existing_records = await self._qdrant.scroll_files(repo_id=repo_id)
            existing_ids = {record.id for record in existing_records}

            # Find deleted files
            deleted_ids = existing_ids - current_file_ids

            # Delete each deleted file
            for file_id in deleted_ids:
                await self._qdrant.delete_file(file_id)
                logger.info("index_repo_file_deleted", file_id=file_id)

            if deleted_ids:
                logger.info(
                    "index_repo_cleanup_complete",
                    repo_id=repo_id,
                    deleted_count=len(deleted_ids),
                )

            return len(deleted_ids)

        except Exception as e:
            logger.error(
                "index_repo_cleanup_failed",
                repo_id=repo_id,
                error=str(e),
            )
            return 0

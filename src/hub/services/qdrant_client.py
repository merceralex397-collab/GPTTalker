"""Qdrant client wrapper for GPTTalker context storage."""

from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    HnswConfig,
    Match,
    PointStruct,
    Record,
    SearchParams,
    VectorParams,
    WithPayloadInterface,
)

from src.hub.config import HubConfig
from src.shared.logging import get_logger
from src.shared.models import (
    VECTOR_DIMENSION,
    ContextBundlePayload,
    FileIndexPayload,
    IssueIndexPayload,
)

logger = get_logger(__name__)

# Collection naming constants
COLLECTION_FILES = "gpttalker_files"
COLLECTION_ISSUES = "gpttalker_issues"
COLLECTION_SUMMARIES = "gpttalker_summaries"

# HNSW configuration
HNSW_M = 16
HNSW_EF_CONSTRUCT = 128
HNSW_FULL_SCAN_THRESHOLD = 10000


class QdrantClientWrapper:
    """Async Qdrant client wrapper for GPTTalker context storage.

    This class provides a high-level interface for semantic search
    and context storage operations. It wraps the Qdrant client with
    GPTTalker-specific logic and conventions.

    Attributes:
        config: HubConfig with Qdrant connection settings.
    """

    def __init__(self, config: HubConfig) -> None:
        """Initialize the Qdrant client wrapper.

        Args:
            config: HubConfig instance with Qdrant settings.
        """
        self.config = config
        self._client: QdrantClient | None = None

    @property
    def client(self) -> QdrantClient:
        """Get the underlying Qdrant client, initializing if needed.

        Returns:
            QdrantClient instance.

        Raises:
            RuntimeError: If client hasn't been initialized.
        """
        if self._client is None:
            raise RuntimeError("Qdrant client not initialized. Call initialize() first.")
        return self._client

    async def initialize(self) -> None:
        """Initialize the Qdrant client and create collections if they don't exist.

        This method connects to the Qdrant server and ensures that required
        collections exist with proper configuration.
        """
        logger.info(
            "qdrant_initializing",
            host=self.config.qdrant_host,
            port=self.config.qdrant_port,
        )

        try:
            # Initialize Qdrant client
            self._client = QdrantClient(
                host=self.config.qdrant_host,
                port=self.config.qdrant_port,
                timeout=self.config.qdrant_timeout,
                prefer_grpc=False,  # Use HTTP for simplicity
            )

            # Create collections if they don't exist
            await self._ensure_collections()

            logger.info("qdrant_initialized", collections=[COLLECTION_FILES, COLLECTION_ISSUES])

        except Exception as e:
            logger.error("qdrant_initialization_failed", error=str(e))
            raise

    async def close(self) -> None:
        """Close the Qdrant client connection."""
        if self._client is not None:
            logger.info("qdrant_closing")
            # Qdrant client doesn't require explicit close for HTTP
            self._client = None

    async def _ensure_collections(self) -> None:
        """Ensure all required collections exist with proper configuration."""
        # Create files collection
        await self._create_collection_if_not_exists(
            collection_name=COLLECTION_FILES,
            description="Indexed file contents for semantic search",
        )

        # Create issues collection
        await self._create_collection_if_not_exists(
            collection_name=COLLECTION_ISSUES,
            description="Known issues with descriptions for semantic search",
        )

        # Create summaries collection (for code summaries)
        await self._create_collection_if_not_exists(
            collection_name=COLLECTION_SUMMARIES,
            description="Extracted code summaries per file for semantic search",
        )

    async def _create_collection_if_not_exists(
        self,
        collection_name: str,
        description: str = "",
    ) -> None:
        """Create a collection if it doesn't already exist.

        Args:
            collection_name: Name of the collection to create.
            description: Optional description for the collection.
        """
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            exists = any(c.name == collection_name for c in collections)

            if not exists:
                # Create collection with HNSW index
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=VECTOR_DIMENSION,
                        distance=Distance.COSINE,
                    ),
                    hnsw_config=HnswConfig(
                        m=HNSW_M,
                        ef_construct=HNSW_EF_CONSTRUCT,
                        full_scan_threshold=HNSW_FULL_SCAN_THRESHOLD,
                    ),
                )

                # Create payload indexes for filtering
                await self._create_payload_indexes(collection_name)

                logger.info("qdrant_collection_created", collection=collection_name)
            else:
                logger.debug("qdrant_collection_exists", collection=collection_name)

        except UnexpectedResponse as e:
            logger.error(
                "qdrant_collection_creation_failed",
                collection=collection_name,
                error=str(e),
            )
            raise

    async def _create_payload_indexes(self, collection_name: str) -> None:
        """Create payload indexes for efficient filtering.

        Args:
            collection_name: Name of the collection to index.
        """
        # Common indexes for all collections
        common_indexes = {
            "repo_id": "keyword",
            "indexed_at": "datetime",
        }

        # Collection-specific indexes
        if collection_name == COLLECTION_FILES:
            indexes = {
                **common_indexes,
                "node_id": "keyword",
                "extension": "keyword",
                "content_hash": "keyword",
                "language": "keyword",
                "size_bytes": "integer",
            }
        elif collection_name == COLLECTION_ISSUES:
            indexes = {
                **common_indexes,
                "status": "keyword",
                "created_at": "datetime",
                "updated_at": "datetime",
            }
        elif collection_name == COLLECTION_SUMMARIES:
            indexes = {
                **common_indexes,
                "node_id": "keyword",
                "file_id": "keyword",
                "language": "keyword",
                "bundle_id": "keyword",
                "bundle_type": "keyword",
                "created_by": "keyword",
            }
        else:
            indexes = common_indexes

        # Create indexes
        for field, field_type in indexes.items():
            try:
                if field_type == "keyword":
                    self.client.create_payload_index(
                        collection_name=collection_name,
                        field_name=field,
                        field_schema="keyword",
                    )
                elif field_type == "integer":
                    self.client.create_payload_index(
                        collection_name=collection_name,
                        field_name=field,
                        field_schema="integer",
                    )
                elif field_type == "datetime":
                    self.client.create_payload_index(
                        collection_name=collection_name,
                        field_name=field,
                        field_schema="datetime",
                    )
            except Exception as e:
                # Index might already exist, log and continue
                logger.debug(
                    "qdrant_index_creation_skipped",
                    collection=collection_name,
                    field=field,
                    error=str(e),
                )

    # === File Operations ===

    async def upsert_file(
        self,
        file_id: str,
        vector: list[float],
        payload: FileIndexPayload,
    ) -> bool:
        """Add or update a file vector in the collection.

        Args:
            file_id: Unique identifier for the file.
            vector: Embedding vector for the file content.
            payload: Structured metadata for the file.

        Returns:
            True if upsert was successful.

        Raises:
            RuntimeError: If client is not initialized.
        """
        try:
            point = PointStruct(
                id=file_id,
                vector=vector,
                payload=payload.model_dump(mode="json"),
            )

            self.client.upsert(
                collection_name=COLLECTION_FILES,
                points=[point],
            )

            logger.info(
                "qdrant_file_upserted",
                file_id=file_id,
                repo_id=payload.repo_id,
            )
            return True

        except Exception as e:
            logger.error(
                "qdrant_file_upsert_failed",
                file_id=file_id,
                error=str(e),
            )
            raise

    async def search_files(
        self,
        query_vector: list[float],
        repo_id: str | None = None,
        repo_ids: list[str] | None = None,
        node_id: str | None = None,
        extension: str | None = None,
        language: str | None = None,
        limit: int = 10,
        score_threshold: float | None = None,
    ) -> list[Record]:
        """Search for files using semantic similarity.

        Args:
            query_vector: Embedding vector to search with.
            repo_id: Optional filter by single repository ID.
            repo_ids: Optional filter by list of repository IDs (for access control).
            node_id: Optional filter by node ID.
            extension: Optional filter by file extension.
            language: Optional filter by programming language.
            limit: Maximum number of results to return.
            score_threshold: Minimum similarity score to return.

        Returns:
            List of matching records with payloads.
        """
        # Build filter conditions
        must_conditions = []

        # Handle repo_id and repo_ids - repo_ids takes precedence for access control
        if repo_ids:
            # Use should for OR logic across multiple repo_ids (access control)
            should_conditions = [{"key": "repo_id", "match": {"value": rid}} for rid in repo_ids]
            must_conditions.append({"should": should_conditions, "min_should": 1})
        elif repo_id:
            must_conditions.append({"key": "repo_id", "match": {"value": repo_id}})

        if node_id:
            must_conditions.append({"key": "node_id", "match": {"value": node_id}})
        if extension:
            must_conditions.append({"key": "extension", "match": {"value": extension}})
        if language:
            must_conditions.append({"key": "language", "match": {"value": language}})

        search_params = SearchParams(
            hnsw_ef=128,
            exact=False,
        )

        results = self.client.search(
            collection_name=COLLECTION_FILES,
            query_vector=query_vector,
            query_filter={"must": must_conditions} if must_conditions else None,
            limit=limit,
            score_threshold=score_threshold,
            with_payload=WithPayloadInterface(True),
            search_params=search_params,
        )

        return list(results)

    async def delete_file(self, file_id: str) -> bool:
        """Delete a file vector from the collection.

        Args:
            file_id: Unique identifier for the file.

        Returns:
            True if deletion was successful.
        """
        try:
            self.client.delete(
                collection_name=COLLECTION_FILES,
                points_selector=[file_id],
            )

            logger.info("qdrant_file_deleted", file_id=file_id)
            return True

        except Exception as e:
            logger.error(
                "qdrant_file_delete_failed",
                file_id=file_id,
                error=str(e),
            )
            return False

    async def get_file(self, file_id: str) -> Record | None:
        """Get a file record by ID.

        Args:
            file_id: Unique identifier for the file.

        Returns:
            Record if found, None otherwise.
        """
        try:
            result = self.client.retrieve(
                collection_name=COLLECTION_FILES,
                ids=[file_id],
                with_payload=WithPayloadInterface(True),
            )
            return result[0] if result else None

        except Exception as e:
            logger.error(
                "qdrant_file_get_failed",
                file_id=file_id,
                error=str(e),
            )
            return None

    async def scroll_files(
        self,
        repo_id: str,
        limit: int = 1000,
    ) -> list[Record]:
        """Scroll through all files for a specific repo.

        Uses pagination to retrieve all files for a given repo_id.

        Args:
            repo_id: Repository ID to filter by.
            limit: Maximum records to return.

        Returns:
            List of file records.
        """
        all_records: list[Record] = []
        offset = None

        while True:
            try:
                result = self.client.scroll(
                    collection_name=COLLECTION_FILES,
                    scroll_filter=Filter(
                        must=[
                            FieldCondition(
                                key="repo_id",
                                match=Match(value=repo_id),
                            )
                        ]
                    ),
                    limit=limit,
                    offset=offset,
                    with_payload=WithPayloadInterface(True),
                )

                records, next_offset = result

                all_records.extend(list(records))

                if next_offset is None:
                    break

                offset = next_offset

                # Safety check for very large repos
                if len(all_records) > 100_000:
                    logger.warning(
                        "qdrant_scroll_files_limit_reached",
                        repo_id=repo_id,
                        count=len(all_records),
                    )
                    break

            except Exception as e:
                logger.error(
                    "qdrant_scroll_files_failed",
                    repo_id=repo_id,
                    error=str(e),
                )
                break

        logger.info(
            "qdrant_scroll_files_complete",
            repo_id=repo_id,
            count=len(all_records),
        )

        return all_records

    # === Issue Operations ===

    async def upsert_issue(
        self,
        issue_id: str,
        vector: list[float],
        payload: IssueIndexPayload,
    ) -> bool:
        """Add or update an issue vector in the collection.

        Args:
            issue_id: Unique identifier for the issue.
            vector: Embedding vector for the issue content.
            payload: Structured metadata for the issue.

        Returns:
            True if upsert was successful.
        """
        try:
            point = PointStruct(
                id=issue_id,
                vector=vector,
                payload=payload.model_dump(mode="json"),
            )

            self.client.upsert(
                collection_name=COLLECTION_ISSUES,
                points=[point],
            )

            logger.info(
                "qdrant_issue_upserted",
                issue_id=issue_id,
                repo_id=payload.repo_id,
            )
            return True

        except Exception as e:
            logger.error(
                "qdrant_issue_upsert_failed",
                issue_id=issue_id,
                error=str(e),
            )
            raise

    async def search_issues(
        self,
        query_vector: list[float],
        repo_id: str | None = None,
        status: str | None = None,
        limit: int = 10,
        score_threshold: float | None = None,
    ) -> list[Record]:
        """Search for issues using semantic similarity.

        Args:
            query_vector: Embedding vector to search with.
            repo_id: Optional filter by repository ID.
            status: Optional filter by issue status.
            limit: Maximum number of results to return.
            score_threshold: Minimum similarity score to return.

        Returns:
            List of matching records with payloads.
        """
        # Build filter conditions
        must_conditions = []

        if repo_id:
            must_conditions.append({"key": "repo_id", "match": {"value": repo_id}})
        if status:
            must_conditions.append({"key": "status", "match": {"value": status}})

        search_params = SearchParams(
            hnsw_ef=128,
            exact=False,
        )

        results = self.client.search(
            collection_name=COLLECTION_ISSUES,
            query_vector=query_vector,
            query_filter={"must": must_conditions} if must_conditions else None,
            limit=limit,
            score_threshold=score_threshold,
            with_payload=WithPayloadInterface(True),
            search_params=search_params,
        )

        return list(results)

    async def delete_issue(self, issue_id: str) -> bool:
        """Delete an issue vector from the collection.

        Args:
            issue_id: Unique identifier for the issue.

        Returns:
            True if deletion was successful.
        """
        try:
            self.client.delete(
                collection_name=COLLECTION_ISSUES,
                points_selector=[issue_id],
            )

            logger.info("qdrant_issue_deleted", issue_id=issue_id)
            return True

        except Exception as e:
            logger.error(
                "qdrant_issue_delete_failed",
                issue_id=issue_id,
                error=str(e),
            )
            return False

    # === Bundle Operations ===

    async def upsert_bundle(
        self,
        bundle_id: str,
        vector: list[float],
        payload: ContextBundlePayload,
    ) -> bool:
        """Add or update a context bundle in the collection.

        Args:
            bundle_id: Unique identifier for the bundle.
            vector: Embedding vector for the bundle (derived from title/description).
            payload: Structured metadata for the bundle.

        Returns:
            True if upsert was successful.
        """
        try:
            point = PointStruct(
                id=bundle_id,
                vector=vector,
                payload=payload.model_dump(mode="json"),
            )

            self.client.upsert(
                collection_name=COLLECTION_SUMMARIES,
                points=[point],
            )

            logger.info(
                "qdrant_bundle_upserted",
                bundle_id=bundle_id,
                bundle_type=payload.bundle_type,
            )
            return True

        except Exception as e:
            logger.error(
                "qdrant_bundle_upsert_failed",
                bundle_id=bundle_id,
                error=str(e),
            )
            raise

    async def get_bundle(self, bundle_id: str) -> Record | None:
        """Get a bundle record by ID.

        Args:
            bundle_id: Unique identifier for the bundle.

        Returns:
            Record if found, None otherwise.
        """
        try:
            result = self.client.retrieve(
                collection_name=COLLECTION_SUMMARIES,
                ids=[bundle_id],
                with_payload=WithPayloadInterface(True),
            )
            return result[0] if result else None

        except Exception as e:
            logger.error(
                "qdrant_bundle_get_failed",
                bundle_id=bundle_id,
                error=str(e),
            )
            return None

    async def search_bundles(
        self,
        query_vector: list[float],
        bundle_type: str | None = None,
        repo_id: str | None = None,
        limit: int = 10,
        score_threshold: float | None = None,
    ) -> list[Record]:
        """Search for bundles using semantic similarity.

        Args:
            query_vector: Embedding vector to search with.
            bundle_type: Optional filter by bundle type.
            repo_id: Optional filter by repository ID.
            limit: Maximum number of results to return.
            score_threshold: Minimum similarity score to return.

        Returns:
            List of matching records with payloads.
        """
        # Build filter conditions
        must_conditions = []

        if bundle_type:
            must_conditions.append({"key": "bundle_type", "match": {"value": bundle_type}})
        if repo_id:
            must_conditions.append({"key": "repo_ids", "match": {"value": repo_id}})

        search_params = SearchParams(
            hnsw_ef=128,
            exact=False,
        )

        results = self.client.search(
            collection_name=COLLECTION_SUMMARIES,
            query_vector=query_vector,
            query_filter={"must": must_conditions} if must_conditions else None,
            limit=limit,
            score_threshold=score_threshold,
            with_payload=WithPayloadInterface(True),
            search_params=search_params,
        )

        return list(results)

    async def scroll_bundles(
        self,
        bundle_type: str | None = None,
        repo_id: str | None = None,
        limit: int = 100,
    ) -> list[Record]:
        """Scroll through bundles with optional filters.

        Args:
            bundle_type: Optional filter by bundle type.
            repo_id: Optional filter by repository ID.
            limit: Maximum records to return.

        Returns:
            List of bundle records.
        """
        must_conditions = []

        if bundle_type:
            must_conditions.append(
                FieldCondition(
                    key="bundle_type",
                    match=Match(value=bundle_type),
                )
            )
        if repo_id:
            must_conditions.append(
                FieldCondition(
                    key="repo_ids",
                    match=Match(value=repo_id),
                )
            )

        scroll_filter = Filter(must=must_conditions) if must_conditions else None

        all_records: list[Record] = []
        offset = None

        while True:
            try:
                result = self.client.scroll(
                    collection_name=COLLECTION_SUMMARIES,
                    scroll_filter=scroll_filter,
                    limit=limit,
                    offset=offset,
                    with_payload=WithPayloadInterface(True),
                )

                records, next_offset = result

                all_records.extend(list(records))

                if next_offset is None:
                    break

                offset = next_offset

                # Safety check for very large results
                if len(all_records) > 10_000:
                    logger.warning(
                        "qdrant_scroll_bundles_limit_reached",
                        count=len(all_records),
                    )
                    break

            except Exception as e:
                logger.error(
                    "qdrant_scroll_bundles_failed",
                    error=str(e),
                )
                break

        return all_records

    async def delete_bundle(self, bundle_id: str) -> bool:
        """Delete a bundle from the collection.

        Args:
            bundle_id: Unique identifier for the bundle.

        Returns:
            True if deletion was successful.
        """
        try:
            self.client.delete(
                collection_name=COLLECTION_SUMMARIES,
                points_selector=[bundle_id],
            )

            logger.info("qdrant_bundle_deleted", bundle_id=bundle_id)
            return True

        except Exception as e:
            logger.error(
                "qdrant_bundle_delete_failed",
                bundle_id=bundle_id,
                error=str(e),
            )
            return False

    # === Collection Info ===

    async def get_collection_info(self, collection_name: str) -> dict[str, Any]:
        """Get information about a collection.

        Args:
            collection_name: Name of the collection.

        Returns:
            Dictionary with collection statistics.
        """
        try:
            info = self.client.get_collection(collection_name)
            return {
                "name": info.name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status.name,
                "indexed_vectors_count": info.indexed_vectors_count,
            }
        except Exception as e:
            logger.error(
                "qdrant_collection_info_failed",
                collection=collection_name,
                error=str(e),
            )
            return {}

    async def health_check(self) -> dict[str, Any]:
        """Check Qdrant connectivity and collection status.

        Returns:
            Dictionary with health status for each collection.
        """
        health = {
            "connected": False,
            "collections": {},
        }

        try:
            # Check connectivity
            collections = self.client.get_collections()
            health["connected"] = True

            # Get info for each collection
            for collection in collections.collections:
                info = await self.get_collection_info(collection.name)
                health["collections"][collection.name] = info

        except Exception as e:
            logger.error("qdrant_health_check_failed", error=str(e))
            health["error"] = str(e)

        return health


# Global client instance
_qdrant_client: QdrantClientWrapper | None = None


def get_qdrant_client(config: HubConfig) -> QdrantClientWrapper:
    """Get or create the global Qdrant client instance.

    This factory function follows the singleton pattern to ensure
    a single client instance is shared across the application.

    Args:
        config: HubConfig instance with Qdrant settings.

    Returns:
        QdrantClientWrapper instance.
    """
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClientWrapper(config)
    return _qdrant_client


async def create_qdrant_client(config: HubConfig) -> QdrantClientWrapper:
    """Create and initialize a new Qdrant client instance.

    This async factory is used during application startup to create
    and initialize the client.

    Args:
        config: HubConfig instance with Qdrant settings.

    Returns:
        Initialized QdrantClientWrapper instance.
    """
    client = QdrantClientWrapper(config)
    await client.initialize()
    return client

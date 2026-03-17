"""Architecture service for generating architecture maps and project landscape outputs."""

from datetime import datetime
from typing import Any

from src.hub.services.qdrant_client import QdrantClientWrapper
from src.shared.logging import get_logger
from src.shared.models import (
    ArchitectureEdge,
    ArchitectureMap,
    ArchitectureNode,
    LandscapeMetadata,
    LandscapeSource,
    RepoOwner,
)
from src.shared.repositories.relationships import RelationshipRepository, RepoOwnerRepository
from src.shared.repositories.repos import RepoRepository

logger = get_logger(__name__)


class ArchitectureService:
    """Service for generating architecture maps and project landscape outputs.

    This service provides high-level operations for creating architecture
    views that combine cross-repo context with relationship metadata,
    including language distribution, owner information, and source citations.
    """

    def __init__(
        self,
        qdrant_client: QdrantClientWrapper,
        repo_repo: RepoRepository,
        relationship_repo: RelationshipRepository | None = None,
        owner_repo: RepoOwnerRepository | None = None,
    ) -> None:
        """Initialize the architecture service.

        Args:
            qdrant_client: Qdrant client for querying indexed files.
            repo_repo: Repository for repo access validation.
            relationship_repo: Optional relationship repository for explicit relationships.
            owner_repo: Optional owner repository for owner metadata.
        """
        self.qdrant_client = qdrant_client
        self.repo_repo = repo_repo
        self.relationship_repo = relationship_repo
        self.owner_repo = owner_repo

    async def get_architecture_map(
        self,
        repo_ids: list[str] | None = None,
        include_relationships: bool = True,
        include_inferred: bool = True,
        max_depth: int = 3,
    ) -> dict[str, Any]:
        """Generate a complete architecture map with nodes, edges, and metadata.

        This method builds an architecture view that includes:
        - Repository nodes with language distribution and file counts
        - Explicit and optionally inferred relationships as edges
        - Owner metadata and source citations

        Args:
            repo_ids: Optional list of repository IDs to include. If None,
                     includes all accessible repos.
            include_relationships: Whether to include explicit relationships as edges.
            include_inferred: Whether to include inferred relationships (future).
            max_depth: Maximum depth for dependency traversal (future use).

        Returns:
            Dictionary with architecture map and metadata.
        """
        # Get accessible repos for access control
        try:
            all_repos = await self.repo_repo.list_all()
            accessible_repo_map = {r.repo_id: r for r in all_repos}
        except Exception as e:
            logger.error("get_architecture_map_get_repos_failed", error=str(e))
            return {
                "success": False,
                "error": "Failed to retrieve accessible repositories",
            }

        # Determine which repos to include
        if repo_ids:
            # Validate requested repos are accessible
            included_repo_ids = [rid for rid in repo_ids if rid in accessible_repo_map]
            if not included_repo_ids:
                logger.warning(
                    "get_architecture_map_no_accessible_repos",
                    requested=repo_ids,
                )
                return {
                    "success": False,
                    "error": "No accessible repositories found for the requested repo_ids",
                }
        else:
            # Include all accessible repos
            included_repo_ids = list(accessible_repo_map.keys())

        # Get owners if available
        owners_map: dict[str, RepoOwner] = {}
        if self.owner_repo:
            try:
                owners_map = await self.owner_repo.list_all()
            except Exception as e:
                logger.warning("get_architecture_map_get_owners_failed", error=str(e))

        # Build architecture nodes
        nodes: list[ArchitectureNode] = []
        total_files = 0
        language_summary: dict[str, int] = {}
        sources: list[LandscapeSource] = []

        for repo_id in included_repo_ids:
            repo = accessible_repo_map.get(repo_id)
            if not repo:
                continue

            # Get language distribution and file count from Qdrant
            language_dist: dict[str, int] = {}
            file_count = 0

            try:
                files = await self.qdrant_client.scroll_files(
                    repo_id=repo_id,
                    limit=1000,
                )
                file_count = len(files)

                # Count files by extension/language
                for record in files:
                    payload = record.payload or {}
                    extension = payload.get("extension", "")
                    language = payload.get("language")

                    # Use language if available, otherwise derive from extension
                    if language:
                        lang_key = language.lower()
                    elif extension:
                        lang_key = self._extension_to_language(extension)
                    else:
                        lang_key = "unknown"

                    language_dist[lang_key] = language_dist.get(lang_key, 0) + 1

            except Exception as e:
                logger.warning(
                    "get_architecture_map_scroll_files_failed",
                    repo_id=repo_id,
                    error=str(e),
                )

            # Get issue count (would need separate query - defaulting to 0)
            issue_count = 0

            # Get owner for this repo
            owner = owners_map.get(repo_id)

            # Add source citation for this repo
            sources.append(
                LandscapeSource(
                    source_type="repo",
                    source_id=repo_id,
                    repo_id=repo_id,
                    node_id=repo.node_id,
                    citation=f"Repository: {repo.name} on node {repo.node_id}",
                    included_at=datetime.utcnow(),
                )
            )

            node = ArchitectureNode(
                repo_id=repo_id,
                node_id=repo.node_id,
                name=repo.name,
                language_distribution=language_dist,
                file_count=file_count,
                issue_count=issue_count,
                owner=owner,
            )
            nodes.append(node)

            total_files += file_count

            # Aggregate language distribution
            for lang, count in language_dist.items():
                language_summary[lang] = language_summary.get(lang, 0) + count

        # Build architecture edges from explicit relationships
        edges: list[ArchitectureEdge] = []
        relationship_count = 0
        if include_relationships and self.relationship_repo and len(nodes) > 1:
            try:
                all_relationships = await self.relationship_repo.list_all()
                relationship_count = len(all_relationships)

                for rel in all_relationships:
                    # Only include relationships where both source and target are in our nodes
                    if (
                        rel.source_repo_id in included_repo_ids
                        and rel.target_repo_id in included_repo_ids
                    ):
                        # Add source citation for this relationship
                        sources.append(
                            LandscapeSource(
                                source_type="relationship",
                                source_id=rel.relationship_id,
                                repo_id=rel.source_repo_id,
                                node_id="",
                                citation=f"Relationship: {rel.source_repo_id} {rel.relationship_type.value} {rel.target_repo_id}",
                                included_at=datetime.utcnow(),
                            )
                        )

                        edge = ArchitectureEdge(
                            source_repo_id=rel.source_repo_id,
                            target_repo_id=rel.target_repo_id,
                            relationship_type=rel.relationship_type,
                            confidence=rel.confidence,
                            description=rel.description,
                        )
                        edges.append(edge)

            except Exception as e:
                logger.warning(
                    "get_architecture_map_get_relationships_failed",
                    error=str(e),
                )

        # Build landscape metadata with ownership and sources
        primary_owner: RepoOwner | None = None
        maintainers: list[RepoOwner] = []

        for owner in owners_map.values():
            if owner.role == "maintainer":
                maintainers.append(owner)
                if primary_owner is None:
                    primary_owner = owner

        landscape_metadata = LandscapeMetadata(
            owner=primary_owner,
            maintainers=maintainers,
            sources=sources,
            relationship_count=relationship_count,
            description="Architecture map with ownership and relationship metadata",
        )

        # Build the architecture map
        architecture_map = ArchitectureMap(
            nodes=nodes,
            edges=edges,
            total_repos=len(nodes),
            total_files=total_files,
            language_summary=language_summary,
            landscape_metadata=landscape_metadata,
        )

        logger.info(
            "get_architecture_map_success",
            total_repos=len(nodes),
            total_edges=len(edges),
            total_files=total_files,
        )

        return {
            "success": True,
            **architecture_map.model_dump(),
        }

    async def get_repo_architecture(
        self,
        repo_id: str,
        include_dependencies: bool = False,
    ) -> dict[str, Any]:
        """Get architecture summary for a single repository.

        This method returns a focused view of a single repo's architecture,
        including its language distribution, file counts, owner, and
        optional dependency information.

        Args:
            repo_id: Repository ID to get architecture for.
            include_dependencies: Whether to include dependency information (future).

        Returns:
            Dictionary with single-repo architecture information.
        """
        # Validate the repo exists and is accessible
        try:
            repo = await self.repo_repo.get(repo_id)
            if not repo:
                return {
                    "success": False,
                    "error": f"Repository not found: {repo_id}",
                }
        except Exception as e:
            logger.error("get_repo_architecture_get_repo_failed", error=str(e))
            return {
                "success": False,
                "error": "Failed to validate repository access",
            }

        # Get owner if available
        owner: RepoOwner | None = None
        if self.owner_repo:
            try:
                owners_map = await self.owner_repo.list_all()
                owner = owners_map.get(repo_id)
            except Exception as e:
                logger.warning(
                    "get_repo_architecture_get_owner_failed",
                    repo_id=repo_id,
                    error=str(e),
                )

        # Get language distribution and file count from Qdrant
        language_dist: dict[str, int] = {}
        file_count = 0

        try:
            files = await self.qdrant_client.scroll_files(
                repo_id=repo_id,
                limit=1000,
            )
            file_count = len(files)

            # Count files by extension/language
            for record in files:
                payload = record.payload or {}
                extension = payload.get("extension", "")
                language = payload.get("language")

                # Use language if available, otherwise derive from extension
                if language:
                    lang_key = language.lower()
                elif extension:
                    lang_key = self._extension_to_language(extension)
                else:
                    lang_key = "unknown"

                language_dist[lang_key] = language_dist.get(lang_key, 0) + 1

        except Exception as e:
            logger.warning(
                "get_repo_architecture_scroll_files_failed",
                repo_id=repo_id,
                error=str(e),
            )

        # Get issue count (would need separate query - defaulting to 0)
        issue_count = 0

        # Build source citation
        sources: list[LandscapeSource] = [
            LandscapeSource(
                source_type="repo",
                source_id=repo_id,
                repo_id=repo_id,
                node_id=repo.node_id,
                citation=f"Repository: {repo.name} on node {repo.node_id}",
                included_at=datetime.utcnow(),
            )
        ]

        # Build the architecture node
        node = ArchitectureNode(
            repo_id=repo_id,
            node_id=repo.node_id,
            name=repo.name,
            language_distribution=language_dist,
            file_count=file_count,
            issue_count=issue_count,
            owner=owner,
        )

        # Build landscape metadata
        landscape_metadata = LandscapeMetadata(
            owner=owner,
            maintainers=[owner] if owner else [],
            sources=sources,
            relationship_count=0,
            description=f"Architecture summary for repository: {repo.name}",
        )

        # Build architecture map for this single repo
        architecture_map = ArchitectureMap(
            nodes=[node],
            edges=[],
            total_repos=1,
            total_files=file_count,
            language_summary=language_dist,
            landscape_metadata=landscape_metadata,
        )

        logger.info(
            "get_repo_architecture_success",
            repo_id=repo_id,
            file_count=file_count,
        )

        return {
            "success": True,
            **architecture_map.model_dump(),
        }

    def _extension_to_language(self, extension: str) -> str:
        """Map file extension to programming language.

        Args:
            extension: File extension (e.g., '.py', '.js').

        Returns:
            Normalized language name.
        """
        # Common extension to language mapping
        extension_map: dict[str, str] = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".java": "java",
            ".c": "c",
            ".cpp": "cpp",
            ".cc": "cpp",
            ".cxx": "cpp",
            ".h": "c",
            ".hpp": "cpp",
            ".cs": "csharp",
            ".go": "go",
            ".rs": "rust",
            ".rb": "ruby",
            ".php": "php",
            ".swift": "swift",
            ".kt": "kotlin",
            ".scala": "scala",
            ".r": "r",
            ".m": "objective-c",
            ".mm": "objective-c",
            ".html": "html",
            ".htm": "html",
            ".css": "css",
            ".scss": "scss",
            ".sass": "sass",
            ".less": "less",
            ".json": "json",
            ".xml": "xml",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".toml": "toml",
            ".md": "markdown",
            ".txt": "text",
            ".sh": "shell",
            ".bash": "shell",
            ".zsh": "shell",
            ".fish": "shell",
            ".sql": "sql",
            ".graphql": "graphql",
            ".gql": "graphql",
            ".vue": "vue",
            ".svelte": "svelte",
            ".dockerfile": "dockerfile",
            ".makefile": "makefile",
            ".gradle": "gradle",
            ".groovy": "groovy",
        }

        # Normalize extension (ensure it starts with dot)
        if not extension.startswith("."):
            extension = "." + extension

        return extension_map.get(extension.lower(), extension.lstrip("."))

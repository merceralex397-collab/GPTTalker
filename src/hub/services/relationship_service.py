"""Relationship service for managing explicit repo relationships."""

import uuid
from datetime import datetime
from typing import Any

from src.shared.logging import get_logger
from src.shared.models import (
    LandscapeMetadata,
    LandscapeSource,
    RepoOwner,
    RepoRelationship,
    RelationshipType,
)
from src.shared.repositories.relationships import RelationshipRepository, RepoOwnerRepository
from src.shared.repositories.repos import RepoRepository

logger = get_logger(__name__)


class RelationshipService:
    """Service for managing repo relationships.

    This service provides high-level operations for creating and managing
    explicit relationships between repositories, including owner tracking
    and landscape metadata with source citations.
    """

    def __init__(
        self,
        relationship_repo: RelationshipRepository,
        owner_repo: RepoOwnerRepository,
        repo_repo: RepoRepository,
    ) -> None:
        """Initialize the relationship service.

        Args:
            relationship_repo: Repository for relationship CRUD operations.
            owner_repo: Repository for owner CRUD operations.
            repo_repo: Repository for validating repo existence.
        """
        self.relationship_repo = relationship_repo
        self.owner_repo = owner_repo
        self.repo_repo = repo_repo

    async def create_relationship(
        self,
        source_repo_id: str,
        target_repo_id: str,
        relationship_type: RelationshipType,
        created_by: str,
        description: str | None = None,
        source_record: str | None = None,
        confidence: float = 1.0,
        bidirectional: bool = False,
    ) -> dict[str, Any]:
        """Create a new explicit relationship.

        Args:
            source_repo_id: Source repository ID.
            target_repo_id: Target repository ID.
            relationship_type: Type of relationship.
            created_by: Who created this relationship (trace_id).
            description: Optional human-readable description.
            source_record: Optional source record citation.
            confidence: Confidence score (0.0-1.0).
            bidirectional: Whether relationship applies both ways.

        Returns:
            Dictionary with success status and relationship data or error.
        """
        # Validate both repos exist
        source_repo = await self.repo_repo.get(source_repo_id)
        if not source_repo:
            logger.warning("create_relationship_source_not_found", repo_id=source_repo_id)
            return {
                "success": False,
                "error": f"Source repository not found: {source_repo_id}",
            }

        target_repo = await self.repo_repo.get(target_repo_id)
        if not target_repo:
            logger.warning("create_relationship_target_not_found", repo_id=target_repo_id)
            return {
                "success": False,
                "error": f"Target repository not found: {target_repo_id}",
            }

        # Create the relationship
        relationship = RepoRelationship(
            relationship_id=str(uuid.uuid4()),
            source_repo_id=source_repo_id,
            target_repo_id=target_repo_id,
            relationship_type=relationship_type,
            description=description,
            confidence=confidence,
            bidirectional=bidirectional,
            created_at=datetime.utcnow(),
            created_by=created_by,
            source_record=source_record,
            metadata={},
        )

        success = await self.relationship_repo.create_relationship(relationship)
        if not success:
            return {
                "success": False,
                "error": "Failed to create relationship",
            }

        logger.info(
            "relationship_created",
            relationship_id=relationship.relationship_id,
            source_repo=source_repo_id,
            target_repo=target_repo_id,
            type=relationship_type.value,
        )

        return {
            "success": True,
            "relationship": relationship.model_dump(),
        }

    async def get_relationships_for_repo(
        self,
        repo_id: str,
        include_incoming: bool = True,
    ) -> list[RepoRelationship]:
        """Get all relationships for a repo.

        Args:
            repo_id: Repository ID to get relationships for.
            include_incoming: Whether to include relationships where repo is target.

        Returns:
            List of relationships involving the repo.
        """
        return await self.relationship_repo.list_by_repo(repo_id, include_incoming)

    async def list_all_relationships(self) -> list[RepoRelationship]:
        """List all explicit relationships.

        Returns:
            List of all relationships.
        """
        return await self.relationship_repo.list_all()

    async def delete_relationship(self, relationship_id: str) -> dict[str, Any]:
        """Delete a relationship.

        Args:
            relationship_id: The relationship ID to delete.

        Returns:
            Dictionary with success status.
        """
        success = await self.relationship_repo.delete_relationship(relationship_id)
        if not success:
            return {
                "success": False,
                "error": "Failed to delete relationship",
            }

        return {
            "success": True,
            "message": f"Relationship {relationship_id} deleted",
        }

    async def add_owner_to_repo(
        self,
        repo_id: str,
        owner_id: str,
        name: str,
        email: str | None = None,
        role: str = "maintainer",
    ) -> dict[str, Any]:
        """Add or update owner for a repo.

        Args:
            repo_id: Repository ID.
            owner_id: Unique owner identifier.
            name: Human-readable owner name.
            email: Optional owner email.
            role: Owner role (maintainer, contributor, observer).

        Returns:
            Dictionary with success status and owner data or error.
        """
        # Validate repo exists
        repo = await self.repo_repo.get(repo_id)
        if not repo:
            logger.warning("add_owner_repo_not_found", repo_id=repo_id)
            return {
                "success": False,
                "error": f"Repository not found: {repo_id}",
            }

        owner = RepoOwner(
            owner_id=owner_id,
            name=name,
            email=email,
            role=role,
            added_at=datetime.utcnow(),
            metadata={},
        )

        success = await self.owner_repo.set_owner(repo_id, owner)
        if not success:
            return {
                "success": False,
                "error": "Failed to set owner",
            }

        logger.info("repo_owner_set", repo_id=repo_id, owner_id=owner_id)

        return {
            "success": True,
            "owner": owner.model_dump(),
        }

    async def get_owner_for_repo(self, repo_id: str) -> RepoOwner | None:
        """Get owner information for a repo.

        Args:
            repo_id: Repository ID.

        Returns:
            Owner information if set, None otherwise.
        """
        return await self.owner_repo.get_owner(repo_id)

    async def get_landscape_with_ownership(
        self,
        include_relationships: bool = True,
    ) -> dict[str, Any]:
        """Get landscape with owner metadata and source citations.

        Args:
            include_relationships: Whether to include explicit relationships.

        Returns:
            Dictionary with landscape data including owners and citations.
        """
        # Get all repos and their owners
        all_repos = await self.repo_repo.list_all()
        all_owners = await self.owner_repo.list_all()

        # Build source citations
        sources: list[LandscapeSource] = []
        for repo in all_repos:
            sources.append(
                LandscapeSource(
                    source_type="repo",
                    source_id=repo.repo_id,
                    repo_id=repo.repo_id,
                    node_id=repo.node_id,
                    citation=f"Repository: {repo.name} on node {repo.node_id}",
                    included_at=datetime.utcnow(),
                )
            )

        # Get explicit relationships if requested
        relationship_count = 0
        if include_relationships:
            relationships = await self.relationship_repo.list_all()
            relationship_count = len(relationships)

            for rel in relationships:
                sources.append(
                    LandscapeSource(
                        source_type="relationship",
                        source_id=rel.relationship_id,
                        repo_id=rel.source_repo_id,
                        node_id="",  # Relationships don't have a single node
                        citation=f"Relationship: {rel.source_repo_id} {rel.relationship_type.value} {rel.target_repo_id}",
                        included_at=datetime.utcnow(),
                    )
                )

        # Get primary owner (first one found)
        primary_owner: RepoOwner | None = None
        maintainers: list[RepoOwner] = []

        # Get maintainers from owners
        for repo_id, owner in all_owners.items():
            if owner.role == "maintainer":
                maintainers.append(owner)
                if primary_owner is None:
                    primary_owner = owner

        landscape_metadata = LandscapeMetadata(
            owner=primary_owner,
            maintainers=maintainers,
            sources=sources,
            relationship_count=relationship_count,
            description="Project landscape with ownership and relationship metadata",
        )

        logger.info(
            "landscape_with_ownership_retrieved",
            total_repos=len(all_repos),
            total_owners=len(all_owners),
            relationship_count=relationship_count,
        )

        return {
            "success": True,
            "landscape_metadata": landscape_metadata.model_dump(),
            "relationship_count": relationship_count,
            "owner_count": len(all_owners),
        }

"""Relationship management tool handlers for MCP protocol."""

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from src.shared.logging import get_logger

if TYPE_CHECKING:
    from src.shared.repositories.relationships import RelationshipRepository, RepoOwnerRepository
    from src.shared.repositories.repos import RepoRepository

logger = get_logger(__name__)


class CreateRelationshipParams(BaseModel):
    """Parameters for creating a repo relationship."""

    source_repo_id: str = Field(..., description="Source repository ID")
    target_repo_id: str = Field(..., description="Target repository ID")
    relationship_type: str = Field(
        ...,
        description="Type of relationship: depends_on, related_to, forks_from, contains, references, shared_dep",
        enum=["depends_on", "related_to", "forks_from", "contains", "references", "shared_dep"],
    )
    description: str | None = Field(None, description="Relationship description")
    source_record: str | None = Field(
        None, description="Source of this relationship (e.g., 'git log', 'import scan', 'manual')"
    )
    confidence: float = Field(1.0, description="Confidence score", ge=0.0, le=1.0)
    bidirectional: bool = Field(False, description="Whether relationship applies both ways")


class ListRelationshipsParams(BaseModel):
    """Parameters for listing repo relationships."""

    repo_id: str | None = Field(
        None,
        description="Repository ID to list relationships for. If omitted, lists all relationships.",
    )
    include_incoming: bool = Field(
        True,
        description="Include relationships where repo is target (only applies if repo_id provided)",
    )
    relationship_type: str | None = Field(
        None,
        description="Filter by relationship type",
        enum=["depends_on", "related_to", "forks_from", "contains", "references", "shared_dep"],
    )


class DeleteRelationshipParams(BaseModel):
    """Parameters for deleting a relationship."""

    relationship_id: str = Field(..., description="Relationship ID to delete")


class SetRepoOwnerParams(BaseModel):
    """Parameters for setting repo owner."""

    repo_id: str = Field(..., description="Repository ID")
    owner_id: str = Field(..., description="Owner identifier")
    name: str = Field(..., description="Owner name")
    email: str | None = Field(None, description="Owner email")
    role: str = Field(
        "maintainer",
        description="Owner role",
        enum=["maintainer", "contributor", "observer"],
    )


class GetRepoOwnerParams(BaseModel):
    """Parameters for getting repo owner."""

    repo_id: str = Field(..., description="Repository ID")


async def create_relationship_handler(
    params: CreateRelationshipParams,
    relationship_repo: "RelationshipRepository | None" = None,
    owner_repo: "RepoOwnerRepository | None" = None,
    repo_repo: "RepoRepository | None" = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    """Create an explicit repo relationship.

    This tool creates a persistent relationship between two repositories
    with provenance tracking. Validates that both repos exist in the registry.

    Args:
        params: Tool parameters.
        relationship_repo: RelationshipRepository for storage.
        owner_repo: RepoOwnerRepository (unused but required for DI).
        repo_repo: RepoRepository for validation.
        trace_id: Trace ID for request tracking.

    Returns:
        Dictionary with success status and relationship data or error.
    """
    # Validate dependencies
    if not all([relationship_repo, repo_repo]):
        logger.error("create_relationship_handler_missing_dependencies")
        return {
            "success": False,
            "error": "Required dependencies not available",
        }

    # Import here to avoid circular dependencies
    from src.shared.models import RelationshipType

    # Validate both repos exist
    source_repo = await repo_repo.get(params.source_repo_id)
    if not source_repo:
        logger.warning("create_relationship_source_not_found", repo_id=params.source_repo_id)
        return {
            "success": False,
            "error": f"Source repository not found: {params.source_repo_id}",
        }

    target_repo = await repo_repo.get(params.target_repo_id)
    if not target_repo:
        logger.warning("create_relationship_target_not_found", repo_id=params.target_repo_id)
        return {
            "success": False,
            "error": f"Target repository not found: {params.target_repo_id}",
        }

    # Create the relationship using the repository directly
    import uuid
    from datetime import datetime

    relationship_type = RelationshipType(params.relationship_type)

    from src.shared.models import RepoRelationship

    relationship = RepoRelationship(
        relationship_id=str(uuid.uuid4()),
        source_repo_id=params.source_repo_id,
        target_repo_id=params.target_repo_id,
        relationship_type=relationship_type,
        description=params.description,
        confidence=params.confidence,
        bidirectional=params.bidirectional,
        created_at=datetime.utcnow(),
        created_by=trace_id or "unknown",
        source_record=params.source_record,
        metadata={},
    )

    success = await relationship_repo.create_relationship(relationship)
    if not success:
        return {
            "success": False,
            "error": "Failed to create relationship",
        }

    logger.info(
        "relationship_created",
        relationship_id=relationship.relationship_id,
        source_repo=params.source_repo_id,
        target_repo=params.target_repo_id,
        type=params.relationship_type,
    )

    return {
        "success": True,
        "relationship": relationship.model_dump(),
    }


async def list_relationships_handler(
    params: ListRelationshipsParams,
    relationship_repo: "RelationshipRepository | None" = None,
) -> dict[str, Any]:
    """List relationships for a repo or all relationships.

    This tool lists explicit relationships, optionally filtered by repo
    or relationship type.

    Args:
        params: Tool parameters.
        relationship_repo: RelationshipRepository for storage.

    Returns:
        Dictionary with list of relationships.
    """
    # Validate dependencies
    if not relationship_repo:
        logger.error("list_relationships_handler_missing_dependencies")
        return {
            "success": False,
            "error": "Required dependencies not available",
        }

    # Import here to avoid circular dependencies
    from src.shared.models import RelationshipType

    relationships = []

    if params.repo_id:
        # Get relationships for specific repo
        relationships = await relationship_repo.list_by_repo(
            params.repo_id,
            params.include_incoming,
        )
    elif params.relationship_type:
        # Get relationships by type
        rel_type = RelationshipType(params.relationship_type)
        relationships = await relationship_repo.list_by_type(rel_type)
    else:
        # Get all relationships
        relationships = await relationship_repo.list_all()

    logger.info(
        "list_relationships_success",
        repo_id=params.repo_id,
        relationship_type=params.relationship_type,
        count=len(relationships),
    )

    return {
        "success": True,
        "relationships": [r.model_dump() for r in relationships],
        "count": len(relationships),
    }


async def delete_relationship_handler(
    params: DeleteRelationshipParams,
    relationship_repo: "RelationshipRepository | None" = None,
) -> dict[str, Any]:
    """Delete a relationship.

    Args:
        params: Tool parameters.
        relationship_repo: RelationshipRepository for storage.

    Returns:
        Dictionary with success status.
    """
    if not relationship_repo:
        logger.error("delete_relationship_handler_missing_dependencies")
        return {
            "success": False,
            "error": "Required dependencies not available",
        }

    success = await relationship_repo.delete_relationship(params.relationship_id)
    if not success:
        return {
            "success": False,
            "error": "Failed to delete relationship",
        }

    logger.info("relationship_deleted", relationship_id=params.relationship_id)

    return {
        "success": True,
        "message": f"Relationship {params.relationship_id} deleted",
    }


async def set_repo_owner_handler(
    params: SetRepoOwnerParams,
    owner_repo: "RepoOwnerRepository | None" = None,
    repo_repo: "RepoRepository | None" = None,
) -> dict[str, Any]:
    """Set owner information for a repository.

    This tool sets or updates owner information for a repository,
    including name, email, and role.

    Args:
        params: Tool parameters.
        owner_repo: RepoOwnerRepository for storage.
        repo_repo: RepoRepository for validation.

    Returns:
        Dictionary with success status and owner data or error.
    """
    # Validate dependencies
    if not all([owner_repo, repo_repo]):
        logger.error("set_repo_owner_handler_missing_dependencies")
        return {
            "success": False,
            "error": "Required dependencies not available",
        }

    # Validate repo exists
    repo = await repo_repo.get(params.repo_id)
    if not repo:
        logger.warning("set_repo_owner_repo_not_found", repo_id=params.repo_id)
        return {
            "success": False,
            "error": f"Repository not found: {params.repo_id}",
        }

    from datetime import datetime

    from src.shared.models import RepoOwner

    owner = RepoOwner(
        owner_id=params.owner_id,
        name=params.name,
        email=params.email,
        role=params.role,
        added_at=datetime.utcnow(),
        metadata={},
    )

    success = await owner_repo.set_owner(params.repo_id, owner)
    if not success:
        return {
            "success": False,
            "error": "Failed to set owner",
        }

    logger.info("repo_owner_set", repo_id=params.repo_id, owner_id=params.owner_id)

    return {
        "success": True,
        "owner": owner.model_dump(),
    }


async def get_repo_owner_handler(
    params: GetRepoOwnerParams,
    owner_repo: "RepoOwnerRepository | None" = None,
) -> dict[str, Any]:
    """Get owner information for a repository.

    Args:
        params: Tool parameters.
        owner_repo: RepoOwnerRepository for storage.

    Returns:
        Dictionary with owner information or error.
    """
    if not owner_repo:
        logger.error("get_repo_owner_handler_missing_dependencies")
        return {
            "success": False,
            "error": "Required dependencies not available",
        }

    owner = await owner_repo.get_owner(params.repo_id)

    if not owner:
        return {
            "success": True,
            "owner": None,
            "message": f"No owner set for repository {params.repo_id}",
        }

    return {
        "success": True,
        "owner": owner.model_dump(),
    }

"""Relationship repository for managing explicit repo relationships."""

import json
from datetime import datetime
from typing import Any

from src.shared.database import DatabaseManager
from src.shared.logging import get_logger
from src.shared.models import RepoOwner, RepoRelationship, RelationshipType

logger = get_logger(__name__)


class RelationshipRepository:
    """SQLite repository for managing explicit repo relationships.

    This repository handles CRUD operations for explicit relationships
    between repositories, stored persistently with provenance.
    """

    def __init__(self, db: DatabaseManager) -> None:
        """Initialize the relationship repository.

        Args:
            db: DatabaseManager instance for database operations.
        """
        self.db = db

    async def create_relationship(self, relationship: RepoRelationship) -> bool:
        """Insert a new relationship.

        Args:
            relationship: The relationship to create.

        Returns:
            True if successful, False otherwise.
        """
        try:
            await self.db.connection.execute(
                """
                INSERT INTO relationships (
                    relationship_id, source_repo_id, target_repo_id, relationship_type,
                    description, confidence, bidirectional, created_at, created_by,
                    source_record, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    relationship.relationship_id,
                    relationship.source_repo_id,
                    relationship.target_repo_id,
                    relationship.relationship_type.value,
                    relationship.description,
                    relationship.confidence,
                    int(relationship.bidirectional),
                    relationship.created_at.isoformat(),
                    relationship.created_by,
                    relationship.source_record,
                    json.dumps(relationship.metadata),
                ),
            )
            await self.db.connection.commit()
            logger.info(
                "relationship_created",
                relationship_id=relationship.relationship_id,
                source_repo=relationship.source_repo_id,
                target_repo=relationship.target_repo_id,
                relationship_type=relationship.relationship_type.value,
            )
            return True
        except Exception as e:
            logger.error("relationship_create_failed", error=str(e))
            return False

    async def get_relationship(self, relationship_id: str) -> RepoRelationship | None:
        """Get a relationship by ID.

        Args:
            relationship_id: The relationship ID to retrieve.

        Returns:
            The relationship if found, None otherwise.
        """
        try:
            cursor = await self.db.connection.execute(
                "SELECT * FROM relationships WHERE relationship_id = ?",
                (relationship_id,),
            )
            row = await cursor.fetchone()
            if row:
                return self._row_to_relationship(row)
            return None
        except Exception as e:
            logger.error("relationship_get_failed", error=str(e), relationship_id=relationship_id)
            return None

    async def list_by_repo(
        self,
        repo_id: str,
        include_incoming: bool = True,
    ) -> list[RepoRelationship]:
        """List all relationships for a repo (as source or target).

        Args:
            repo_id: The repository ID to list relationships for.
            include_incoming: Whether to include relationships where repo is target.

        Returns:
            List of relationships involving the repo.
        """
        try:
            if include_incoming:
                cursor = await self.db.connection.execute(
                    """
                    SELECT * FROM relationships
                    WHERE source_repo_id = ? OR target_repo_id = ?
                    ORDER BY created_at DESC
                    """,
                    (repo_id, repo_id),
                )
            else:
                cursor = await self.db.connection.execute(
                    """
                    SELECT * FROM relationships
                    WHERE source_repo_id = ?
                    ORDER BY created_at DESC
                    """,
                    (repo_id,),
                )
            rows = await cursor.fetchall()
            return [self._row_to_relationship(row) for row in rows]
        except Exception as e:
            logger.error("relationship_list_by_repo_failed", error=str(e), repo_id=repo_id)
            return []

    async def list_by_type(
        self,
        relationship_type: RelationshipType,
    ) -> list[RepoRelationship]:
        """List all relationships of a specific type.

        Args:
            relationship_type: The type of relationship to filter by.

        Returns:
            List of relationships of the specified type.
        """
        try:
            cursor = await self.db.connection.execute(
                """
                SELECT * FROM relationships
                WHERE relationship_type = ?
                ORDER BY created_at DESC
                """,
                (relationship_type.value,),
            )
            rows = await cursor.fetchall()
            return [self._row_to_relationship(row) for row in rows]
        except Exception as e:
            logger.error(
                "relationship_list_by_type_failed",
                error=str(e),
                relationship_type=relationship_type.value,
            )
            return []

    async def update_relationship(
        self,
        relationship_id: str,
        **updates: Any,
    ) -> bool:
        """Update relationship fields.

        Args:
            relationship_id: The relationship ID to update.
            **updates: Fields to update.

        Returns:
            True if successful, False otherwise.
        """
        if not updates:
            return False

        try:
            set_clauses = []
            values = []
            for key, value in updates.items():
                if key == "relationship_type" and isinstance(value, RelationshipType):
                    set_clauses.append(f"{key} = ?")
                    values.append(value.value)
                elif key == "bidirectional":
                    set_clauses.append(f"{key} = ?")
                    values.append(int(value))
                elif key == "metadata":
                    set_clauses.append(f"{key} = ?")
                    values.append(json.dumps(value))
                else:
                    set_clauses.append(f"{key} = ?")
                    values.append(value)

            values.append(relationship_id)
            query = f"UPDATE relationships SET {', '.join(set_clauses)} WHERE relationship_id = ?"
            await self.db.connection.execute(query, values)
            await self.db.connection.commit()
            logger.info("relationship_updated", relationship_id=relationship_id)
            return True
        except Exception as e:
            logger.error(
                "relationship_update_failed", error=str(e), relationship_id=relationship_id
            )
            return False

    async def delete_relationship(self, relationship_id: str) -> bool:
        """Delete a relationship.

        Args:
            relationship_id: The relationship ID to delete.

        Returns:
            True if successful, False otherwise.
        """
        try:
            await self.db.connection.execute(
                "DELETE FROM relationships WHERE relationship_id = ?",
                (relationship_id,),
            )
            await self.db.connection.commit()
            logger.info("relationship_deleted", relationship_id=relationship_id)
            return True
        except Exception as e:
            logger.error(
                "relationship_delete_failed", error=str(e), relationship_id=relationship_id
            )
            return False

    async def find_relationships(
        self,
        source_repo_id: str | None = None,
        target_repo_id: str | None = None,
        relationship_type: RelationshipType | None = None,
    ) -> list[RepoRelationship]:
        """Search relationships with filters.

        Args:
            source_repo_id: Filter by source repository ID.
            target_repo_id: Filter by target repository ID.
            relationship_type: Filter by relationship type.

        Returns:
            List of matching relationships.
        """
        try:
            conditions = []
            values = []

            if source_repo_id:
                conditions.append("source_repo_id = ?")
                values.append(source_repo_id)
            if target_repo_id:
                conditions.append("target_repo_id = ?")
                values.append(target_repo_id)
            if relationship_type:
                conditions.append("relationship_type = ?")
                values.append(relationship_type.value)

            query = "SELECT * FROM relationships"
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " ORDER BY created_at DESC"

            cursor = await self.db.connection.execute(query, values)
            rows = await cursor.fetchall()
            return [self._row_to_relationship(row) for row in rows]
        except Exception as e:
            logger.error("relationship_find_failed", error=str(e))
            return []

    async def list_all(self) -> list[RepoRelationship]:
        """List all relationships.

        Returns:
            List of all relationships.
        """
        try:
            cursor = await self.db.connection.execute(
                "SELECT * FROM relationships ORDER BY created_at DESC"
            )
            rows = await cursor.fetchall()
            return [self._row_to_relationship(row) for row in rows]
        except Exception as e:
            logger.error("relationship_list_all_failed", error=str(e))
            return []

    def _row_to_relationship(self, row: tuple[Any, ...]) -> RepoRelationship:
        """Convert a database row to a RepoRelationship model.

        Args:
            row: Database row tuple.

        Returns:
            RepoRelationship model instance.
        """
        return RepoRelationship(
            relationship_id=row[0],
            source_repo_id=row[1],
            target_repo_id=row[2],
            relationship_type=RelationshipType(row[3]),
            description=row[4],
            confidence=row[5],
            bidirectional=bool(row[6]),
            created_at=datetime.fromisoformat(row[7]),
            created_by=row[8],
            source_record=row[9],
            metadata=json.loads(row[10]) if row[10] else {},
        )


class RepoOwnerRepository:
    """SQLite repository for managing repo owners.

    This repository handles CRUD operations for repository owner information.
    """

    def __init__(self, db: DatabaseManager) -> None:
        """Initialize the repo owner repository.

        Args:
            db: DatabaseManager instance for database operations.
        """
        self.db = db

    async def set_owner(self, repo_id: str, owner: RepoOwner) -> bool:
        """Set or update owner for a repository.

        Args:
            repo_id: The repository ID.
            owner: The owner information to set.

        Returns:
            True if successful, False otherwise.
        """
        try:
            await self.db.connection.execute(
                """
                INSERT OR REPLACE INTO repo_owners (
                    repo_id, owner_id, name, email, role, added_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    repo_id,
                    owner.owner_id,
                    owner.name,
                    owner.email,
                    owner.role,
                    owner.added_at.isoformat(),
                    json.dumps(owner.metadata),
                ),
            )
            await self.db.connection.commit()
            logger.info("repo_owner_set", repo_id=repo_id, owner_id=owner.owner_id)
            return True
        except Exception as e:
            logger.error("repo_owner_set_failed", error=str(e), repo_id=repo_id)
            return False

    async def get_owner(self, repo_id: str) -> RepoOwner | None:
        """Get owner information for a repository.

        Args:
            repo_id: The repository ID.

        Returns:
            Owner information if found, None otherwise.
        """
        try:
            cursor = await self.db.connection.execute(
                "SELECT * FROM repo_owners WHERE repo_id = ?",
                (repo_id,),
            )
            row = await cursor.fetchone()
            if row:
                return self._row_to_owner(row)
            return None
        except Exception as e:
            logger.error("repo_owner_get_failed", error=str(e), repo_id=repo_id)
            return None

    async def delete_owner(self, repo_id: str) -> bool:
        """Delete owner information for a repository.

        Args:
            repo_id: The repository ID.

        Returns:
            True if successful, False otherwise.
        """
        try:
            await self.db.connection.execute(
                "DELETE FROM repo_owners WHERE repo_id = ?",
                (repo_id,),
            )
            await self.db.connection.commit()
            logger.info("repo_owner_deleted", repo_id=repo_id)
            return True
        except Exception as e:
            logger.error("repo_owner_delete_failed", error=str(e), repo_id=repo_id)
            return False

    async def list_all(self) -> dict[str, RepoOwner]:
        """List all repo owners.

        Returns:
            Dictionary mapping repo_id to owner information.
        """
        try:
            cursor = await self.db.connection.execute("SELECT * FROM repo_owners")
            rows = await cursor.fetchall()
            return {row[0]: self._row_to_owner(row) for row in rows}
        except Exception as e:
            logger.error("repo_owner_list_all_failed", error=str(e))
            return {}

    def _row_to_owner(self, row: tuple[Any, ...]) -> RepoOwner:
        """Convert a database row to a RepoOwner model.

        Args:
            row: Database row tuple.

        Returns:
            RepoOwner model instance.
        """
        return RepoOwner(
            owner_id=row[1],
            name=row[2],
            email=row[3],
            role=row[4],
            added_at=datetime.fromisoformat(row[5]),
            metadata=json.loads(row[6]) if row[6] else {},
        )

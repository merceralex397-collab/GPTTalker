"""Session store for managing conversation state with OpenCode and other LLM services."""

import time
from datetime import datetime
from typing import Any

from src.shared.logging import get_logger

logger = get_logger(__name__)


class SessionStore:
    """In-memory store for OpenCode session state.

    This store maintains conversation history, working directory context,
    and metadata for each active session. Sessions are keyed by session_id
    and optionally filtered by service.

    Note: This is an in-memory implementation. For production, consider
    swapping to Redis or another distributed store.
    """

    def __init__(self, max_history: int = 50):
        """Initialize the session store.

        Args:
            max_history: Maximum number of messages to retain per session.
        """
        self._sessions: dict[str, dict[str, Any]] = {}
        self._max_history = max_history

    async def create_session(
        self,
        session_id: str,
        service_id: str,
        working_dir: str | None = None,
    ) -> dict[str, Any]:
        """Create a new session with conversation history.

        Args:
            session_id: Unique session identifier.
            service_id: LLM service identifier for this session.
            working_dir: Optional working directory for file operations.

        Returns:
            Created session data.
        """
        now = datetime.utcnow()
        session = {
            "session_id": session_id,
            "service_id": service_id,
            "messages": [],
            "working_dir": working_dir,
            "created_at": now,
            "updated_at": now,
            "metadata": {},
        }
        self._sessions[session_id] = session
        logger.info("session_created", session_id=session_id, service_id=service_id)
        return self._serialize_session(session)

    async def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Get a session by ID.

        Args:
            session_id: Session identifier.

        Returns:
            Session data or None if not found.
        """
        session = self._sessions.get(session_id)
        if session is None:
            logger.debug("session_not_found", session_id=session_id)
            return None
        return self._serialize_session(session)

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Add a message to the session conversation history.

        Args:
            session_id: Session identifier.
            role: Message role ("user", "assistant", "system").
            content: Message content.
            metadata: Optional metadata for the message.

        Returns:
            Updated session data or None if session not found.
        """
        session = self._sessions.get(session_id)
        if session is None:
            logger.warning("session_not_found_for_message", session_id=session_id)
            return None

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }

        # Add message and enforce max history limit
        session["messages"].append(message)
        if len(session["messages"]) > self._max_history:
            session["messages"] = session["messages"][-self._max_history :]

        session["updated_at"] = datetime.utcnow()

        logger.debug(
            "message_added",
            session_id=session_id,
            role=role,
            message_count=len(session["messages"]),
        )

        return self._serialize_session(session)

    async def get_history(
        self,
        session_id: str,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Get conversation history for a session.

        Args:
            session_id: Session identifier.
            limit: Optional limit on number of messages to return.

        Returns:
            List of messages in chronological order.
        """
        session = self._sessions.get(session_id)
        if session is None:
            return []

        messages = session["messages"]
        if limit is not None and limit > 0:
            messages = messages[-limit:]

        return messages

    async def update_working_dir(
        self,
        session_id: str,
        working_dir: str,
    ) -> dict[str, Any] | None:
        """Update the working directory for a session.

        Args:
            session_id: Session identifier.
            working_dir: New working directory path.

        Returns:
            Updated session data or None if session not found.
        """
        session = self._sessions.get(session_id)
        if session is None:
            logger.warning("session_not_found_for_working_dir", session_id=session_id)
            return None

        session["working_dir"] = working_dir
        session["updated_at"] = datetime.utcnow()

        logger.info("working_dir_updated", session_id=session_id, working_dir=working_dir)
        return self._serialize_session(session)

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session and cleanup.

        Args:
            session_id: Session identifier.

        Returns:
            True if session was deleted, False if not found.
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info("session_deleted", session_id=session_id)
            return True
        return False

    async def list_sessions(self, service_id: str | None = None) -> list[dict[str, Any]]:
        """List all sessions, optionally filtered by service.

        Args:
            service_id: Optional service ID to filter by.

        Returns:
            List of session data.
        """
        sessions = []
        for session in self._sessions.values():
            if service_id is None or session.get("service_id") == service_id:
                sessions.append(self._serialize_session(session))
        return sessions

    async def cleanup_expired(self, max_age_seconds: int = 3600) -> int:
        """Clean up sessions that haven't been updated recently.

        Args:
            max_age_seconds: Maximum age in seconds since last update.

        Returns:
            Number of sessions cleaned up.
        """
        now = time.time()
        expired_ids = []

        for session_id, session in self._sessions.items():
            last_update = session["updated_at"].timestamp()
            if now - last_update > max_age_seconds:
                expired_ids.append(session_id)

        for session_id in expired_ids:
            del self._sessions[session_id]
            logger.info("session_expired", session_id=session_id)

        if expired_ids:
            logger.info("cleanup_completed", removed_count=len(expired_ids))

        return len(expired_ids)

    def _serialize_session(self, session: dict[str, Any]) -> dict[str, Any]:
        """Serialize session for return (exclude internal fields).

        Args:
            session: Internal session dict.

        Returns:
            Serialized session data.
        """
        return {
            "session_id": session["session_id"],
            "service_id": session["service_id"],
            "messages": session["messages"],
            "working_dir": session["working_dir"],
            "created_at": session["created_at"].isoformat(),
            "updated_at": session["updated_at"].isoformat(),
            "metadata": session["metadata"],
        }

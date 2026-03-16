"""Operation scope definitions for policy engine.

This module defines the operation scopes (read/write/execute) and
validation context used throughout the policy engine.
"""

from dataclasses import dataclass
from enum import StrEnum

from src.shared.logging import get_logger

logger = get_logger(__name__)


class OperationScope(StrEnum):
    """Defines the type of operation being performed.

    These scopes are used to determine which policy checks apply
    and to separate read and write access controls.
    """

    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"


@dataclass
class ValidationContext:
    """Context for policy validation.

    This context is passed through the validation chain to provide
    information about the operation being performed.

    Attributes:
        scope: The type of operation (read/write/execute).
        trace_id: Optional trace ID for request tracking.
        caller: Source of the request (e.g., tool name, MCP caller).
    """

    scope: OperationScope
    trace_id: str | None = None
    caller: str | None = None

    def to_log_dict(self) -> dict:
        """Convert context to dictionary for logging.

        Returns:
            Dict with context information.
        """
        result: dict = {
            "scope": self.scope.value,
        }
        if self.trace_id:
            result["trace_id"] = self.trace_id
        if self.caller:
            result["caller"] = self.caller
        return result


class ScopeValidator:
    """Utility class for validating operation scopes.

    Provides helper methods for scope-based access control decisions.
    """

    # Define which scopes allow read operations
    READ_SCOPES = {OperationScope.READ}

    # Define which scopes allow write operations
    WRITE_SCOPES = {OperationScope.WRITE}

    # Define which scopes allow execute operations
    EXECUTE_SCOPES = {OperationScope.EXECUTE}

    @staticmethod
    def allows_read(scope: OperationScope) -> bool:
        """Check if scope permits read operations.

        Args:
            scope: Operation scope to check.

        Returns:
            True if scope allows read.
        """
        return scope in ScopeValidator.READ_SCOPES

    @staticmethod
    def allows_write(scope: OperationScope) -> bool:
        """Check if scope permits write operations.

        Args:
            scope: Operation scope to check.

        Returns:
            True if scope allows write.
        """
        return scope in ScopeValidator.WRITE_SCOPES

    @staticmethod
    def allows_execute(scope: OperationScope) -> bool:
        """Check if scope permits execute operations.

        Args:
            scope: Operation scope to check.

        Returns:
            True if scope allows execute.
        """
        return scope in ScopeValidator.EXECUTE_SCOPES

    @staticmethod
    def requires_write(scope: OperationScope) -> bool:
        """Check if scope requires write access.

        Args:
            scope: Operation scope to check.

        Returns:
            True if scope requires write access.
        """
        return scope in {OperationScope.WRITE, OperationScope.EXECUTE}

    @staticmethod
    def requires_read(scope: OperationScope) -> bool:
        """Check if scope requires read access.

        Args:
            scope: Operation scope to check.

        Returns:
            True if scope requires read access.
        """
        # All scopes require some form of read access
        return True

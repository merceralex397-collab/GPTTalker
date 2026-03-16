"""Policy engine orchestration layer.

This module provides the unified PolicyEngine that combines all policy
checks (node, repo, write target, LLM service) into a single validation chain.
"""

from dataclasses import dataclass

from src.hub.policy.llm_service_policy import LLMServicePolicy
from src.hub.policy.node_policy import NodeAccessResult, NodePolicy
from src.hub.policy.path_utils import PathNormalizer, PathValidationResult
from src.hub.policy.repo_policy import RepoPolicy
from src.hub.policy.scopes import OperationScope, ValidationContext
from src.hub.policy.write_target_policy import WriteTargetPolicy
from src.shared.exceptions import PathTraversalError
from src.shared.logging import get_logger
from src.shared.models import LLMServiceInfo, RepoInfo, WriteTargetInfo

logger = get_logger(__name__)


@dataclass
class ValidationResult:
    """Result of policy validation operations.

    Attributes:
        allowed: Whether the operation is allowed.
        reason: Human-readable reason for the result (None if allowed).
        scope: The operation scope that was validated.
    """

    allowed: bool
    reason: str | None
    scope: OperationScope


class PolicyEngine:
    """Unified policy engine combining all policy checks.

    Implements fail-closed validation chain:
    1. Node access validation
    2. Repository access validation
    3. Path normalization (for file operations)
    4. Write target validation (for writes)
    5. LLM service validation (for LLM operations)

    Each step must pass before proceeding.
    """

    def __init__(
        self,
        node_policy: NodePolicy,
        repo_policy: RepoPolicy,
        write_target_policy: WriteTargetPolicy,
        llm_service_policy: LLMServicePolicy,
    ):
        """Initialize policy engine with all policy components.

        Args:
            node_policy: NodePolicy for node access control.
            repo_policy: RepoPolicy for repository access control.
            write_target_policy: WriteTargetPolicy for write target control.
            llm_service_policy: LLMServicePolicy for LLM service access.
        """
        self.node_policy = node_policy
        self.repo_policy = repo_policy
        self.write_target_policy = write_target_policy
        self.llm_service_policy = llm_service_policy

    # ==================== Read Operation Validators ====================

    async def validate_node_read(self, node_id: str) -> NodeAccessResult:
        """Validate node access for read operations.

        Args:
            node_id: Node identifier to validate.

        Returns:
            NodeAccessResult with approval status.
        """
        log_context = {"node_id": node_id, "operation": "read"}
        logger.debug("validating_node_read", **log_context)

        result = await self.node_policy.validate_node_access(node_id)

        logger.info(
            "node_read_validation_complete",
            **log_context,
            approved=result.approved,
            rejection_reason=result.rejection_reason,
        )
        return result

    async def validate_repo_read(self, repo_id: str) -> RepoInfo:
        """Validate repository access for read operations.

        Args:
            repo_id: Repository identifier to validate.

        Returns:
            RepoInfo if repository is accessible.

        Raises:
            ValueError: If repository is unknown or inaccessible.
        """
        log_context = {"repo_id": repo_id, "operation": "read"}
        logger.debug("validating_repo_read", **log_context)

        try:
            result = await self.repo_policy.validate_repo_access(repo_id)
            logger.info("repo_read_validation_complete", **log_context)
            return result
        except ValueError as e:
            logger.warning("repo_read_validation_failed", **log_context, error=str(e))
            raise

    async def validate_file_read(
        self, node_id: str, repo_id: str, file_path: str
    ) -> PathValidationResult:
        """Validate file path for read operations.

        Args:
            node_id: Node identifier.
            repo_id: Repository identifier.
            file_path: File path to validate.

        Returns:
            PathValidationResult with normalized path.
        """
        log_context = {
            "node_id": node_id,
            "repo_id": repo_id,
            "file_path": file_path,
            "operation": "file_read",
        }
        logger.debug("validating_file_read", **log_context)

        # Get repo info for base path
        repo = await self.repo_policy.validate_repo_access(repo_id)

        try:
            # Normalize the path relative to repo base
            normalized = PathNormalizer.normalize(file_path, repo.path)

            # Validate no symlink escapes
            PathNormalizer.validate_symlinks(normalized, repo.path)

            result = PathValidationResult(
                normalized_path=normalized,
                is_valid=True,
            )

            logger.info("file_read_validation_complete", **log_context)
            return result

        except PathTraversalError as e:
            logger.warning("file_read_validation_failed", **log_context, error=str(e))
            return PathValidationResult(
                normalized_path=file_path,
                is_valid=False,
                error=str(e),
            )

    # ==================== Write Operation Validators ====================

    async def validate_node_write(self, node_id: str) -> NodeAccessResult:
        """Validate node access for write operations.

        Args:
            node_id: Node identifier to validate.

        Returns:
            NodeAccessResult with approval status.
        """
        log_context = {"node_id": node_id, "operation": "write"}
        logger.debug("validating_node_write", **log_context)

        result = await self.node_policy.validate_node_access(node_id)

        logger.info(
            "node_write_validation_complete",
            **log_context,
            approved=result.approved,
            rejection_reason=result.rejection_reason,
        )
        return result

    async def validate_write_target(self, path: str, extension: str) -> WriteTargetInfo:
        """Validate write target access.

        Args:
            path: Absolute path to write to.
            extension: File extension (e.g., '.md').

        Returns:
            WriteTargetInfo if target is allowed.

        Raises:
            ValueError: If target is unknown or extension not allowed.
        """
        log_context = {"path": path, "extension": extension, "operation": "write"}
        logger.debug("validating_write_target", **log_context)

        try:
            result = await self.write_target_policy.validate_write_access(path, extension)
            logger.info("write_target_validation_complete", **log_context)
            return result
        except ValueError as e:
            logger.warning("write_target_validation_failed", **log_context, error=str(e))
            raise

    async def validate_file_write(
        self, node_id: str, repo_id: str, file_path: str, extension: str
    ) -> PathValidationResult:
        """Validate file path for write operations.

        Args:
            node_id: Node identifier.
            repo_id: Repository identifier.
            file_path: File path to validate.
            extension: File extension.

        Returns:
            PathValidationResult with normalized path.
        """
        log_context = {
            "node_id": node_id,
            "repo_id": repo_id,
            "file_path": file_path,
            "extension": extension,
            "operation": "file_write",
        }
        logger.debug("validating_file_write", **log_context)

        # Get repo info for base path
        repo = await self.repo_policy.validate_repo_access(repo_id)

        try:
            # Normalize the path relative to repo base
            normalized = PathNormalizer.normalize(file_path, repo.path)

            # Validate no symlink escapes
            PathNormalizer.validate_symlinks(normalized, repo.path)

            # Validate extension against allowed list for write target
            # First get write target info (this validates extension)
            await self.write_target_policy.validate_write_access(normalized, extension)

            result = PathValidationResult(
                normalized_path=normalized,
                is_valid=True,
            )

            logger.info("file_write_validation_complete", **log_context)
            return result

        except (PathTraversalError, ValueError) as e:
            logger.warning("file_write_validation_failed", **log_context, error=str(e))
            return PathValidationResult(
                normalized_path=file_path,
                is_valid=False,
                error=str(e),
            )

    # ==================== LLM Operation Validators ====================

    async def validate_llm_service(self, service_id: str) -> LLMServiceInfo:
        """Validate LLM service access.

        Args:
            service_id: Service identifier to validate.

        Returns:
            LLMServiceInfo if service exists and is accessible.

        Raises:
            ValueError: If service is unknown or inaccessible.
        """
        log_context = {"service_id": service_id, "operation": "llm"}
        logger.debug("validating_llm_service", **log_context)

        try:
            result = await self.llm_service_policy.validate_service_access(service_id)
            logger.info("llm_service_validation_complete", **log_context)
            return result
        except ValueError as e:
            logger.warning("llm_service_validation_failed", **log_context, error=str(e))
            raise

    async def validate_llm_service_by_name(self, name: str) -> LLMServiceInfo:
        """Validate LLM service access by name.

        Args:
            name: Service name to validate.

        Returns:
            LLMServiceInfo if service exists and is accessible.

        Raises:
            ValueError: If service is unknown or inaccessible.
        """
        log_context = {"service_name": name, "operation": "llm"}
        logger.debug("validating_llm_service_by_name", **log_context)

        try:
            result = await self.llm_service_policy.validate_service_by_name(name)
            logger.info("llm_service_by_name_validation_complete", **log_context)
            return result
        except ValueError as e:
            logger.warning("llm_service_by_name_validation_failed", **log_context, error=str(e))
            raise

    # ==================== Combined Validation Chains ====================

    async def validate_read_operation(
        self,
        context: ValidationContext,
        node_id: str,
        repo_id: str | None = None,
        file_path: str | None = None,
    ) -> ValidationResult:
        """Validate a complete read operation.

        This is the main entry point for read operations. It validates:
        1. Node access
        2. Repository access (if repo_id provided)
        3. File path (if file_path provided)

        Args:
            context: Validation context with scope and trace info.
            node_id: Node identifier.
            repo_id: Optional repository identifier.
            file_path: Optional file path to validate.

        Returns:
            ValidationResult with allowed status and reason.
        """
        log_context = {
            **context.to_log_dict(),
            "node_id": node_id,
            "repo_id": repo_id,
            "file_path": file_path,
        }
        logger.debug("validating_read_operation", **log_context)

        # Step 1: Validate node access
        node_result = await self.validate_node_read(node_id)
        if not node_result.approved:
            return ValidationResult(
                allowed=False,
                reason=f"Node access denied: {node_result.rejection_reason}",
                scope=OperationScope.READ,
            )

        # Step 2: Validate repo access if provided
        if repo_id:
            try:
                await self.validate_repo_read(repo_id)
            except ValueError as e:
                return ValidationResult(
                    allowed=False,
                    reason=f"Repository access denied: {e}",
                    scope=OperationScope.READ,
                )

        # Step 3: Validate file path if provided
        if file_path and repo_id:
            path_result = await self.validate_file_read(node_id, repo_id, file_path)
            if not path_result.is_valid:
                return ValidationResult(
                    allowed=False,
                    reason=f"File path validation failed: {path_result.error}",
                    scope=OperationScope.READ,
                )

        logger.info("read_operation_validation_passed", **log_context)
        return ValidationResult(
            allowed=True,
            reason=None,
            scope=OperationScope.READ,
        )

    async def validate_write_operation(
        self,
        context: ValidationContext,
        node_id: str,
        path: str,
        extension: str,
    ) -> ValidationResult:
        """Validate a complete write operation.

        This is the main entry point for write operations. It validates:
        1. Node access
        2. Write target access (path + extension)

        Args:
            context: Validation context with scope and trace info.
            node_id: Node identifier.
            path: Absolute path to write to.
            extension: File extension (e.g., '.md').

        Returns:
            ValidationResult with allowed status and reason.
        """
        log_context = {
            **context.to_log_dict(),
            "node_id": node_id,
            "path": path,
            "extension": extension,
        }
        logger.debug("validating_write_operation", **log_context)

        # Step 1: Validate node access
        node_result = await self.validate_node_write(node_id)
        if not node_result.approved:
            return ValidationResult(
                allowed=False,
                reason=f"Node access denied: {node_result.rejection_reason}",
                scope=OperationScope.WRITE,
            )

        # Step 2: Validate write target
        try:
            await self.validate_write_target(path, extension)
        except ValueError as e:
            return ValidationResult(
                allowed=False,
                reason=f"Write target denied: {e}",
                scope=OperationScope.WRITE,
            )

        logger.info("write_operation_validation_passed", **log_context)
        return ValidationResult(
            allowed=True,
            reason=None,
            scope=OperationScope.WRITE,
        )

    async def validate_llm_operation(
        self,
        context: ValidationContext,
        service_id: str | None = None,
        service_name: str | None = None,
    ) -> ValidationResult:
        """Validate a complete LLM operation.

        This is the main entry point for LLM operations. It validates:
        1. LLM service access (by ID or name)

        Args:
            context: Validation context with scope and trace info.
            service_id: Optional service identifier.
            service_name: Optional service name.

        Returns:
            ValidationResult with allowed status and reason.
        """
        log_context = {
            **context.to_log_dict(),
            "service_id": service_id,
            "service_name": service_name,
        }
        logger.debug("validating_llm_operation", **log_context)

        if not service_id and not service_name:
            return ValidationResult(
                allowed=False,
                reason="No service ID or name provided",
                scope=OperationScope.READ,
            )

        # Validate service access
        try:
            if service_id:
                await self.validate_llm_service(service_id)
            else:
                await self.validate_llm_service_by_name(service_name)
        except ValueError as e:
            return ValidationResult(
                allowed=False,
                reason=f"LLM service denied: {e}",
                scope=OperationScope.READ,
            )

        logger.info("llm_operation_validation_passed", **log_context)
        return ValidationResult(
            allowed=True,
            reason=None,
            scope=OperationScope.READ,
        )

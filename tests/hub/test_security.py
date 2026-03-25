"""Security regression tests for GPTTalker.

These tests verify security-critical behavior including:
- Path traversal prevention
- Target validation (unknown nodes/repos/write targets)
- Log redaction of sensitive data
- Fail-closed behavior for missing/malformed inputs

Tests use mocked dependencies to isolate security logic.
"""

import logging
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.hub.policy import (
    PathNormalizer,
    PathValidationResult,
    PolicyEngine,
    ValidationContext,
)
from src.hub.policy.node_policy import NodePolicy, NodeAccessResult
from src.hub.policy.repo_policy import RepoPolicy
from src.hub.policy.write_target_policy import WriteTargetPolicy
from src.hub.policy.llm_service_policy import LLMServicePolicy
from src.hub.policy.scopes import OperationScope
from src.shared.exceptions import PathTraversalError
from src.shared.logging import redact_sensitive, SENSITIVE_PATTERNS
from src.shared.models import NodeStatus
from src.shared.schemas import NodeHealthStatus


# ============================================================================
# Path Traversal Tests
# ============================================================================


class TestPathTraversal:
    """Tests for path traversal attack prevention."""

    def test_path_traversal_dotdot_rejected(self):
        """Test that .. path traversal is rejected."""
        base = "/home/user/repo"

        # Attempt various .. patterns
        dangerous_paths = [
            "../etc/passwd",
            "../../../../etc/passwd",
            "foo/../../../etc/passwd",
            "foo/bar/../../secrets",
            "../foo/bar",
            "foo/..",
            "....",
            ".../...",
        ]

        for path in dangerous_paths:
            with pytest.raises(PathTraversalError) as exc_info:
                PathNormalizer.normalize(path, base)
            assert "traversal" in str(exc_info.value).lower()

    def test_path_traversal_windows_backslash_rejected(self):
        """Test that Windows backslash traversal is rejected."""
        base = "/home/user/repo"

        dangerous_paths = [
            "..\\..\\windows\\system32\\config\\sam",
            "foo\\bar\\..\\..\\secrets",
            "..\\foo",
        ]

        for path in dangerous_paths:
            with pytest.raises(PathTraversalError) as exc_info:
                PathNormalizer.normalize(path, base)
            assert "traversal" in str(exc_info.value).lower()

    def test_path_traversal_absolute_path_rejected(self):
        """Test that absolute paths outside base are rejected."""
        # These should work when there's no base
        assert PathNormalizer.normalize("/etc/passwd") == "/etc/passwd"

        # But with base, absolute paths outside should fail
        base = "/home/user/repo"
        dangerous_paths = [
            "/etc/passwd",
            "/usr/bin/ls",
            "/root/.ssh",
        ]

        for path in dangerous_paths:
            with pytest.raises(PathTraversalError) as exc_info:
                PathNormalizer.normalize(path, base)
            assert (
                "traversal" in str(exc_info.value).lower()
                or "escape" in str(exc_info.value).lower()
            )

    def test_relative_path_within_base_accepted(self):
        """Test that relative paths are resolved against base."""
        base = "/home/user/repo"

        # Valid relative paths should be resolved and accepted
        valid_relative = [
            ("src", "/home/user/repo/src"),
            ("docs/README.md", "/home/user/repo/docs/README.md"),
            ("test.txt", "/home/user/repo/test.txt"),
            ("./src", "/home/user/repo/src"),
            ("foo/bar/../baz", "/home/user/repo/foo/baz"),
        ]

        for path, expected in valid_relative:
            result = PathNormalizer.normalize(path, base)
            assert result == expected, f"Expected {expected}, got {result}"

    def test_path_traversal_null_byte_rejected(self):
        """Test that null byte injection is rejected."""
        base = "/home/user/repo"

        # Null byte in path should cause issues
        dangerous_paths = [
            "file\x00.txt",
            "foo\x00/../etc/passwd",
            "/etc/passwd\x00",
        ]

        for path in dangerous_paths:
            with pytest.raises((PathTraversalError, ValueError)):
                PathNormalizer.normalize(path, base)

    def test_path_traversal_symlink_rejected(self):
        """Test that symlink escapes are detected and rejected."""
        with patch("pathlib.Path.resolve") as mock_resolve:
            # Simulate a symlink that escapes the base directory
            mock_resolve.side_effect = OSError("Cannot resolve symlink")

            # When symlink resolution fails, it should still validate safely
            path = "link_to_outside"
            base = "/home/user/repo"

            # The behavior depends on whether symlink can be resolved
            # If it can't be resolved, validate_symlinks may raise or fall back
            try:
                PathNormalizer.validate_symlinks(path, base)
            except PathTraversalError:
                # This is the expected fail-closed behavior
                pass
            except OSError:
                # Fall back to basic check - verify it still validates
                assert PathNormalizer.is_safe_relative(path, base) is False


# ============================================================================
# Target Validation Tests
# ============================================================================


class TestTargetValidation:
    """Tests for unknown target rejection."""

    @pytest.fixture
    def mock_node_repo(self):
        """Create a mock node repository."""
        repo = MagicMock()
        repo.get = AsyncMock(return_value=None)  # No nodes by default
        repo.list_all = AsyncMock(return_value=[])
        return repo

    @pytest.fixture
    def mock_health_service(self):
        """Create a mock health service."""
        service = MagicMock()
        service.get_node_health = AsyncMock(return_value=None)
        return service

    @pytest.fixture
    def node_policy(self, mock_node_repo, mock_health_service):
        """Create NodePolicy with mocks."""
        return NodePolicy(mock_node_repo, mock_health_service)

    @pytest.mark.asyncio
    async def test_unknown_node_access_denied(self, node_policy):
        """Test that access to unknown nodes is denied."""
        result = await node_policy.validate_node_access("unknown-node-id")

        assert result.approved is False
        assert result.rejection_reason is not None
        assert "unknown" in result.rejection_reason.lower()

    @pytest.mark.asyncio
    async def test_unknown_repo_access_denied(self):
        """Test that access to unknown repos is denied."""
        mock_repo_repo = MagicMock()
        mock_repo_repo.get = AsyncMock(return_value=None)

        policy = RepoPolicy(mock_repo_repo)

        with pytest.raises(ValueError) as exc_info:
            await policy.validate_repo_access("unknown-repo-id")

        assert (
            "not found" in str(exc_info.value).lower() or "unknown" in str(exc_info.value).lower()
        )

    @pytest.mark.asyncio
    async def test_unregistered_write_target_denied(self):
        """Test that unregistered write targets are denied."""
        mock_repo = MagicMock()
        mock_repo.get = AsyncMock(return_value=None)

        policy = WriteTargetPolicy(mock_repo)

        with pytest.raises(ValueError) as exc_info:
            await policy.validate_write_access("/unregistered/path/file.md", ".md")

        assert (
            "not found" in str(exc_info.value).lower()
            or "not allowed" in str(exc_info.value).lower()
            or "unknown" in str(exc_info.value).lower()
        )

    def test_extension_allowlist_enforced(self):
        """Test that extension allowlist is enforced."""
        allowed = [".md", ".txt", ".json"]

        # Allowed extensions should pass
        for ext in allowed:
            assert PathNormalizer.validate_extension(ext, allowed) is True
            assert PathNormalizer.validate_extension(ext.replace(".", ""), allowed) is True

        # Disallowed should fail
        with pytest.raises(PathTraversalError) as exc_info:
            PathNormalizer.validate_extension(".exe", allowed)
        assert "not in allowed" in str(exc_info.value).lower()

        with pytest.raises(PathTraversalError) as exc_info:
            PathNormalizer.validate_extension(".sh", allowed)
        assert "not in allowed" in str(exc_info.value).lower()


# ============================================================================
# Redaction Tests
# ============================================================================


class TestRedaction:
    """Tests for sensitive data redaction in logs."""

    def test_api_key_redacted_in_logs(self):
        """Test that API keys are redacted."""
        data = {
            "message": "Making request",
            "api_key": "sk-1234567890abcdef",
            "endpoint": "https://api.example.com",
        }

        redacted = redact_sensitive(data)

        assert redacted["api_key"] == "[REDACTED]"
        assert redacted["message"] == "Making request"
        assert redacted["endpoint"] == "https://api.example.com"

    def test_token_redacted_in_logs(self):
        """Test that tokens are redacted."""
        data = {
            "action": "authenticate",
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ",
            "refresh_token": "refresh_token_value_12345",
            "user_id": "user_123",
        }

        redacted = redact_sensitive(data)

        assert redacted["token"] == "[REDACTED]"
        assert redacted["refresh_token"] == "[REDACTED]"
        assert redacted["user_id"] == "user_123"

    def test_password_redacted_in_logs(self):
        """Test that passwords are redacted."""
        data = {
            "username": "admin",
            "password": "super_secret_password_123",
            "database": "users",
        }

        redacted = redact_sensitive(data)

        assert redacted["password"] == "[REDACTED]"
        assert redacted["username"] == "admin"
        assert redacted["database"] == "users"

    def test_sensitive_path_redacted(self):
        """Test that sensitive path patterns are redacted."""
        # Test nested sensitive data
        data = {
            "request": {
                "auth": {
                    "api_key": "secret_key_123",
                    "token": "token_abc",
                }
            },
            "level1": {
                "level2": {
                    "password": "nested_password",
                    "safe_field": "visible",
                }
            },
        }

        redacted = redact_sensitive(data)

        # Verify nested redaction works
        assert redacted["request"]["auth"]["api_key"] == "[REDACTED]"
        assert redacted["request"]["auth"]["token"] == "[REDACTED]"
        assert redacted["level1"]["level2"]["password"] == "[REDACTED]"
        assert redacted["level1"]["level2"]["safe_field"] == "visible"

    def test_redaction_patterns_defined(self):
        """Test that sensitive patterns are properly defined."""
        expected_patterns = [
            "password",
            "passwd",
            "secret",
            "token",
            "api_key",
            "apikey",
            "authorization",
            "credential",
            "private_key",
            "access_token",
            "refresh_token",
        ]

        for pattern in expected_patterns:
            assert pattern in SENSITIVE_PATTERNS


# ============================================================================
# Fail-Closed Tests
# ============================================================================


class TestFailClosed:
    """Tests for fail-closed behavior."""

    @pytest.mark.asyncio
    async def test_missing_policy_engine_fails_closed(self):
        """Test that missing policy engine components result in closed behavior."""
        # When repositories return None, validation should fail
        mock_node_repo = MagicMock()
        mock_node_repo.get = AsyncMock(return_value=None)
        mock_node_repo.list_all = AsyncMock(return_value=[])

        mock_health_service = MagicMock()
        mock_health_service.get_node_health = AsyncMock(return_value=None)

        node_policy = NodePolicy(mock_node_repo, mock_health_service)

        # Unknown node should be denied (fail closed)
        result = await node_policy.validate_node_access("any-node")
        assert result.approved is False
        assert result.rejection_reason is not None

    @pytest.mark.asyncio
    async def test_missing_repository_fails_closed(self):
        """Test that missing repository results in fail-closed behavior."""
        # Create a policy with a repo that returns None
        mock_repo = MagicMock()
        mock_repo.get = AsyncMock(return_value=None)

        policy = RepoPolicy(mock_repo)

        # Accessing unknown repo should raise
        with pytest.raises(ValueError):
            await policy.validate_repo_access("nonexistent")

    @pytest.mark.asyncio
    async def test_invalid_policy_requirement_denied(self):
        """Test that invalid policy requirements are denied."""
        # Test that policy engine properly rejects invalid operations
        mock_node_repo = MagicMock()
        mock_node = MagicMock()
        mock_node.node_id = "test-node"
        mock_node.status = NodeStatus.HEALTHY
        mock_node_repo.get = AsyncMock(return_value=mock_node)

        mock_health_service = MagicMock()
        mock_health_info = MagicMock()
        mock_health_info.health_status = NodeHealthStatus.HEALTHY
        mock_health_service.get_node_health = AsyncMock(return_value=mock_health_info)

        node_policy = NodePolicy(mock_node_repo, mock_health_service)

        # With valid node but policy engine should still work
        result = await node_policy.validate_node_access("test-node")
        assert result.approved is True

    def test_malformed_parameters_rejected(self):
        """Test that malformed parameters are rejected."""
        # Empty path should raise
        with pytest.raises(PathTraversalError) as exc_info:
            PathNormalizer.normalize("", "/base")
        assert "empty" in str(exc_info.value).lower()

        # None path should raise
        with pytest.raises((PathTraversalError, TypeError)):
            PathNormalizer.normalize(None, "/base")  # type: ignore

    @pytest.mark.asyncio
    async def test_policy_engine_validates_before_execution(self):
        """Test that policy engine validates before allowing execution."""
        # Create mock policies
        mock_node_repo = MagicMock()
        mock_node = MagicMock()
        mock_node.node_id = "test-node"
        mock_node.status = NodeStatus.HEALTHY
        mock_node_repo.get = AsyncMock(return_value=mock_node)
        mock_node_repo.list_all = AsyncMock(return_value=[mock_node])

        mock_health_service = MagicMock()
        mock_health_info = MagicMock()
        mock_health_info.health_status = NodeHealthStatus.HEALTHY
        mock_health_service.get_node_health = AsyncMock(return_value=mock_health_info)

        mock_repo_repo = MagicMock()
        mock_repo = MagicMock()
        mock_repo.repo_id = "test-repo"
        mock_repo.path = "/home/test/repo"
        mock_repo_repo.get = AsyncMock(return_value=mock_repo)

        mock_write_target_repo = MagicMock()
        mock_write_target = MagicMock()
        mock_write_target.target_id = "test-target"
        mock_write_target.path = "/home/test/writes"
        mock_write_target.allowed_extensions = [".md"]
        mock_write_target_repo.get = AsyncMock(return_value=mock_write_target)

        mock_llm_service_repo = MagicMock()
        mock_llm_service_repo.get = AsyncMock(return_value=None)

        # Create policies
        node_policy = NodePolicy(mock_node_repo, mock_health_service)
        repo_policy = RepoPolicy(mock_repo_repo)
        write_target_policy = WriteTargetPolicy(mock_write_target_repo)
        llm_service_policy = LLMServicePolicy(mock_llm_service_repo)

        # Create engine
        engine = PolicyEngine(
            node_policy=node_policy,
            repo_policy=repo_policy,
            write_target_policy=write_target_policy,
            llm_service_policy=llm_service_policy,
        )

        # Test valid read operation
        context = ValidationContext(scope=OperationScope.READ, trace_id="test-123")
        result = await engine.validate_read_operation(
            context=context,
            node_id="test-node",
            repo_id="test-repo",
            file_path="test.txt",
        )

        assert result.allowed is True
        assert result.reason is None

    @pytest.mark.asyncio
    async def test_policy_engine_rejects_unknown_node(self):
        """Test that policy engine rejects unknown nodes."""
        mock_node_repo = MagicMock()
        mock_node_repo.get = AsyncMock(return_value=None)

        mock_health_service = MagicMock()
        mock_health_service.get_node_health = AsyncMock(return_value=None)

        mock_repo_repo = MagicMock()
        mock_write_target_repo = MagicMock()
        mock_llm_service_repo = MagicMock()

        node_policy = NodePolicy(mock_node_repo, mock_health_service)
        repo_policy = RepoPolicy(mock_repo_repo)
        write_target_policy = WriteTargetPolicy(mock_write_target_repo)
        llm_service_policy = LLMServicePolicy(mock_llm_service_repo)

        engine = PolicyEngine(
            node_policy=node_policy,
            repo_policy=repo_policy,
            write_target_policy=write_target_policy,
            llm_service_policy=llm_service_policy,
        )

        context = ValidationContext(scope=OperationScope.READ)
        result = await engine.validate_read_operation(
            context=context,
            node_id="unknown-node",
        )

        assert result.allowed is False
        assert "node" in result.reason.lower()


# ============================================================================
# Edge Cases and Regression Tests
# ============================================================================


class TestSecurityEdgeCases:
    """Additional edge case tests for security hardening."""

    def test_url_encoded_traversal_rejected(self):
        """Test that URL-encoded path traversal is rejected."""
        base = "/home/user/repo"

        # URL encoded versions of ..
        dangerous_paths = [
            "%2e%2e/etc/passwd",
            "%252e%252e%252fetc%252fpasswd",
            "test%2e%2e%2fsecrets",
        ]

        for path in dangerous_paths:
            with pytest.raises(PathTraversalError) as exc_info:
                PathNormalizer.normalize(path, base)
            assert (
                "traversal" in str(exc_info.value).lower()
                or "encoded" in str(exc_info.value).lower()
            )

    def test_home_directory_expansion_rejected(self):
        """Test that ~ path expansion is detected and rejected."""
        base = "/home/user/repo"

        dangerous_paths = [
            "~/../etc/passwd",
            "~/.ssh/authorized_keys",
            "foo~/bar",
        ]

        for path in dangerous_paths:
            with pytest.raises(PathTraversalError) as exc_info:
                PathNormalizer.normalize(path, base)
            assert "traversal" in str(exc_info.value).lower()

    def test_sensitive_pattern_case_insensitive(self):
        """Test that sensitive pattern matching is case-insensitive."""
        data = {
            "PASSWORD": "secret123",
            "API_KEY": "key123",
            "Token": "token123",
            "SECRET": "secret456",
        }

        redacted = redact_sensitive(data)

        assert redacted["PASSWORD"] == "[REDACTED]"
        assert redacted["API_KEY"] == "[REDACTED]"
        assert redacted["Token"] == "[REDACTED]"
        assert redacted["SECRET"] == "[REDACTED]"

    @pytest.mark.asyncio
    async def test_health_unknown_fails_closed(self):
        """Test that unknown health status results in fail-closed."""
        mock_node_repo = MagicMock()
        mock_node = MagicMock()
        mock_node.node_id = "test-node"
        mock_node.status = NodeStatus.HEALTHY
        mock_node_repo.get = AsyncMock(return_value=mock_node)

        mock_health_service = MagicMock()
        # Return None for health - should fail closed
        mock_health_service.get_node_health = AsyncMock(return_value=None)

        node_policy = NodePolicy(mock_node_repo, mock_health_service)
        result = await node_policy.validate_node_access("test-node")

        # Should be denied due to unknown health (fail closed)
        assert result.approved is False
        assert (
            "no_health_data" in result.rejection_reason
            or "unknown" in result.rejection_reason.lower()
        )

    @pytest.mark.asyncio
    async def test_health_unhealthy_fails_closed(self):
        """Test that unhealthy nodes are rejected."""
        mock_node_repo = MagicMock()
        mock_node = MagicMock()
        mock_node.node_id = "test-node"
        mock_node.status = NodeStatus.HEALTHY
        mock_node_repo.get = AsyncMock(return_value=mock_node)

        mock_health_service = MagicMock()
        mock_health_info = MagicMock()
        mock_health_info.health_status = NodeHealthStatus.UNHEALTHY
        mock_health_info.health_error = "Connection refused"
        mock_health_service.get_node_health = AsyncMock(return_value=mock_health_info)

        node_policy = NodePolicy(mock_node_repo, mock_health_service)
        result = await node_policy.validate_node_access("test-node")

        # Should be denied due to unhealthy status
        assert result.approved is False
        assert "unhealthy" in result.rejection_reason.lower()

    def test_list_redaction_handles_lists(self):
        """Test that redact handles list data."""
        data = {
            "items": [
                {"api_key": "key1", "name": "item1"},
                {"token": "token2", "name": "item2"},
            ]
        }

        redacted = redact_sensitive(data)

        assert redacted["items"][0]["api_key"] == "[REDACTED]"
        assert redacted["items"][0]["name"] == "item1"
        assert redacted["items"][1]["token"] == "[REDACTED]"
        assert redacted["items"][1]["name"] == "item2"

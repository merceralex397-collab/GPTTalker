"""Contract tests for GPTTalker MCP tools.

These tests verify the behavior of MCP tool handlers under various scenarios
including happy paths and failure modes. Tests use mocked dependencies.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.hub.tools.discovery import (
    list_nodes_handler,
    list_repos_handler,
)
from src.hub.tools.inspection import (
    inspect_repo_tree_handler,
    read_repo_file_handler,
)
from src.hub.tools.search import search_repo_handler
from src.hub.tools.markdown import write_markdown_handler
from src.hub.tools.llm import chat_llm_handler
from src.hub.tools.git_operations import git_status_handler


# ============================================================================
# Fixtures for Mock Dependencies
# ============================================================================


@pytest.fixture
def mock_node():
    """Create a mock node object."""
    node = MagicMock()
    node.node_id = "test-node-1"
    node.name = "Test Node"
    node.hostname = "test-node.example.com"
    node.status = "online"
    node.last_seen = datetime.utcnow()
    return node


@pytest.fixture
def mock_repo():
    """Create a mock repo object."""
    repo = MagicMock()
    repo.repo_id = "test-repo-1"
    repo.name = "Test Repo"
    repo.path = "/home/test/repo"
    repo.node_id = "test-node-1"
    repo.is_indexed = False
    return repo


@pytest.fixture
def mock_write_target():
    """Create a mock write target object."""
    target = MagicMock()
    target.target_id = "test-target-1"
    target.path = "/home/test/writes"
    target.allowed_extensions = [".md", ".txt"]
    return target


@pytest.fixture
def mock_llm_service():
    """Create a mock LLM service object."""
    service = MagicMock()
    service.service_id = "test-service-1"
    service.name = "Test LLM"
    service.type = "chat"
    service.endpoint = "http://localhost:8080/v1/chat"
    service.status = "active"
    return service


@pytest.fixture
def mock_node_client():
    """Create a mock HubNodeClient."""
    client = MagicMock()
    client.list_directory = AsyncMock(
        return_value={
            "success": True,
            "entries": [
                {"name": "file1.txt", "type": "file"},
                {"name": "file2.md", "type": "file"},
                {"name": "subdir", "type": "dir"},
            ],
            "total": 3,
        }
    )
    client.read_file = AsyncMock(
        return_value={
            "success": True,
            "content": "Test file content",
            "size_bytes": 18,
            "bytes_read": 18,
            "truncated": False,
        }
    )
    client.search = AsyncMock(
        return_value={
            "success": True,
            "matches": [
                {"file": "test.py", "line": 10, "content": "def test(): pass"},
            ],
            "match_count": 1,
            "files_searched": 5,
        }
    )
    client.git_status = AsyncMock(
        return_value={
            "success": True,
            "branch": "main",
            "is_clean": False,
            "staged": ["file1.txt"],
            "staged_count": 1,
            "modified": ["file2.txt"],
            "modified_count": 1,
            "untracked": [],
            "untracked_count": 0,
            "ahead": 0,
            "behind": 0,
        }
    )
    client.write_file = AsyncMock(
        return_value={
            "success": True,
            "data": {
                "bytes_written": 100,
                "sha256_hash": "abc123",
                "verified": True,
            },
        }
    )
    return client


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM service client."""
    client = MagicMock()
    client.chat = AsyncMock(
        return_value={
            "response": "Test response from LLM",
            "model": "gpt-4",
            "tokens_used": 50,
            "finish_reason": "stop",
        }
    )
    return client


# ============================================================================
# Discovery Tool Tests
# ============================================================================


class TestDiscoveryTools:
    """Tests for list_nodes and list_repos discovery tools."""

    @pytest.mark.asyncio
    async def test_list_nodes_returns_structured_response(self, mock_node):
        """Test that list_nodes returns properly structured response."""
        # Create mock node repository
        mock_node_repo = MagicMock()
        mock_node_repo.list_all = AsyncMock(return_value=[mock_node])
        mock_node_repo.get_health = AsyncMock(
            return_value={
                "health_status": "healthy",
                "health_latency_ms": 10,
                "health_check_count": 5,
                "consecutive_failures": 0,
            }
        )

        # Call handler
        result = await list_nodes_handler(node_repo=mock_node_repo)

        # Verify response structure
        assert "nodes" in result
        assert "total" in result
        assert result["total"] == 1

        node_data = result["nodes"][0]
        assert node_data["node_id"] == "test-node-1"
        assert node_data["name"] == "Test Node"
        assert node_data["hostname"] == "test-node.example.com"
        assert "health" in node_data

    @pytest.mark.asyncio
    async def test_list_nodes_empty_registry(self):
        """Test list_nodes with empty registry returns empty list."""
        mock_node_repo = MagicMock()
        mock_node_repo.list_all = AsyncMock(return_value=[])
        mock_node_repo.get_health = AsyncMock(return_value=None)

        result = await list_nodes_handler(node_repo=mock_node_repo)

        assert result["total"] == 0
        assert result["nodes"] == []

    @pytest.mark.asyncio
    async def test_list_nodes_no_repository(self):
        """Test list_nodes when repository is not available."""
        result = await list_nodes_handler(node_repo=None)

        assert "error" in result
        assert "not available" in result["error"]

    @pytest.mark.asyncio
    async def test_list_repos_returns_structured_response(self, mock_repo):
        """Test that list_repos returns properly structured response."""
        mock_repo_repo = MagicMock()
        mock_repo_repo.list_all = AsyncMock(return_value=[mock_repo])

        result = await list_repos_handler(repo_repo=mock_repo_repo)

        assert "repos" in result
        assert "total" in result
        assert result["total"] == 1

        repo_data = result["repos"][0]
        assert repo_data["repo_id"] == "test-repo-1"
        assert repo_data["name"] == "Test Repo"
        assert repo_data["path"] == "/home/test/repo"
        assert repo_data["node_id"] == "test-node-1"

    @pytest.mark.asyncio
    async def test_list_repos_filtered_by_node(self, mock_repo):
        """Test list_repos with node_id filter."""
        mock_repo_repo = MagicMock()
        mock_repo_repo.list_by_node = AsyncMock(return_value=[mock_repo])

        result = await list_repos_handler(
            node_id="test-node-1",
            repo_repo=mock_repo_repo,
        )

        assert result["filtered_by_node"] == "test-node-1"
        mock_repo_repo.list_by_node.assert_called_once_with("test-node-1")

    @pytest.mark.asyncio
    async def test_list_repos_no_repository(self):
        """Test list_repos when repository is not available."""
        result = await list_repos_handler(repo_repo=None)

        assert "error" in result


# ============================================================================
# Inspection Tool Tests
# ============================================================================


class TestInspectionTools:
    """Tests for inspect_repo_tree and read_repo_file tools."""

    @pytest.mark.asyncio
    async def test_inspect_repo_tree_requires_node_and_repo(
        self,
        mock_node_client,
        mock_node,
        mock_repo,
    ):
        """Test that inspect_repo_tree validates node and repo parameters."""
        # Test with missing node_id
        result = await inspect_repo_tree_handler(
            node_id="",
            repo_id="test-repo-1",
            node_client=mock_node_client,
        )
        assert result["success"] is False
        assert "not found" in result["error"].lower()

        # Test with missing repo_id
        result = await inspect_repo_tree_handler(
            node_id="test-node-1",
            repo_id="",
            node_client=mock_node_client,
        )
        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_inspect_repo_tree_node_not_found(
        self,
        mock_node_client,
    ):
        """Test inspect_repo_tree when node doesn't exist."""
        mock_node_repo = MagicMock()
        mock_node_repo.get = AsyncMock(return_value=None)

        result = await inspect_repo_tree_handler(
            node_id="nonexistent-node",
            repo_id="test-repo-1",
            node_client=mock_node_client,
            node_repo=mock_node_repo,
            repo_repo=MagicMock(),
        )

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_inspect_repo_tree_success(
        self,
        mock_node_client,
        mock_node,
        mock_repo,
    ):
        """Test successful inspect_repo_tree call."""
        mock_node_repo = MagicMock()
        mock_node_repo.get = AsyncMock(return_value=mock_node)

        mock_repo_repo = MagicMock()
        mock_repo_repo.get = AsyncMock(return_value=mock_repo)

        result = await inspect_repo_tree_handler(
            node_id="test-node-1",
            repo_id="test-repo-1",
            path="src",
            max_entries=50,
            node_client=mock_node_client,
            node_repo=mock_node_repo,
            repo_repo=mock_repo_repo,
        )

        assert result["success"] is True
        assert result["repo_id"] == "test-repo-1"
        assert result["node_id"] == "test-node-1"
        assert "entries" in result

    @pytest.mark.asyncio
    async def test_read_repo_file_requires_parameters(
        self,
        mock_node_client,
    ):
        """Test that read_repo_file validates required parameters."""
        # Test with missing file_path
        result = await read_repo_file_handler(
            node_id="test-node-1",
            repo_id="test-repo-1",
            file_path="",
            node_client=mock_node_client,
        )
        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_read_repo_file_success(
        self,
        mock_node_client,
        mock_node,
        mock_repo,
    ):
        """Test successful read_repo_file call."""
        mock_node_repo = MagicMock()
        mock_node_repo.get = AsyncMock(return_value=mock_node)

        mock_repo_repo = MagicMock()
        mock_repo_repo.get = AsyncMock(return_value=mock_repo)

        result = await read_repo_file_handler(
            node_id="test-node-1",
            repo_id="test-repo-1",
            file_path="README.md",
            node_client=mock_node_client,
            node_repo=mock_node_repo,
            repo_repo=mock_repo_repo,
        )

        assert result["success"] is True
        assert "content" in result
        assert result["encoding"] == "utf-8"

    @pytest.mark.asyncio
    async def test_read_repo_file_path_traversal_rejected(
        self,
        mock_node_client,
        mock_node,
        mock_repo,
    ):
        """Test that path traversal is rejected."""
        mock_node_repo = MagicMock()
        mock_node_repo.get = AsyncMock(return_value=mock_node)

        mock_repo_repo = MagicMock()
        mock_repo_repo.get = AsyncMock(return_value=mock_repo)

        # Attempt path traversal
        result = await read_repo_file_handler(
            node_id="test-node-1",
            repo_id="test-repo-1",
            file_path="../../etc/passwd",
            node_client=mock_node_client,
            node_repo=mock_node_repo,
            repo_repo=mock_repo_repo,
        )

        assert result["success"] is False
        assert "validation failed" in result["error"].lower()


# ============================================================================
# Search Tool Tests
# ============================================================================


class TestSearchTools:
    """Tests for search_repo and git_status tools."""

    @pytest.mark.asyncio
    async def test_search_repo_validates_parameters(self, mock_node_client):
        """Test that search_repo validates required parameters."""
        # Test with empty pattern
        mock_node_repo = MagicMock()
        mock_node_repo.get = AsyncMock(return_value=None)

        result = await search_repo_handler(
            node_id="test-node-1",
            repo_id="test-repo-1",
            pattern="",
            node_client=mock_node_client,
            node_repo=mock_node_repo,
            repo_repo=MagicMock(),
        )

        assert result["success"] is False
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_search_repo_success(
        self,
        mock_node_client,
        mock_node,
        mock_repo,
    ):
        """Test successful search_repo call."""
        mock_node_repo = MagicMock()
        mock_node_repo.get = AsyncMock(return_value=mock_node)

        mock_repo_repo = MagicMock()
        mock_repo_repo.get = AsyncMock(return_value=mock_repo)

        result = await search_repo_handler(
            node_id="test-node-1",
            repo_id="test-repo-1",
            pattern="def test",
            node_client=mock_node_client,
            node_repo=mock_node_repo,
            repo_repo=mock_repo_repo,
        )

        assert result["success"] is True
        assert "matches" in result
        assert result["match_count"] >= 0

    @pytest.mark.asyncio
    async def test_search_repo_max_results_clamped(
        self,
        mock_node_client,
        mock_node,
        mock_repo,
    ):
        """Test that max_results is clamped to valid range."""
        mock_node_repo = MagicMock()
        mock_node_repo.get = AsyncMock(return_value=mock_node)

        mock_repo_repo = MagicMock()
        mock_repo_repo.get = AsyncMock(return_value=mock_repo)

        # Request exceeding max
        result = await search_repo_handler(
            node_id="test-node-1",
            repo_id="test-repo-1",
            pattern="test",
            max_results=5000,  # Should be clamped to 1000
            node_client=mock_node_client,
            node_repo=mock_node_repo,
            repo_repo=mock_repo_repo,
        )

        # Should still succeed (clamped internally)
        assert "success" in result

    @pytest.mark.asyncio
    async def test_git_status_returns_proper_format(
        self,
        mock_node_client,
        mock_node,
        mock_repo,
    ):
        """Test that git_status returns properly formatted response."""
        mock_node_repo = MagicMock()
        mock_node_repo.get = AsyncMock(return_value=mock_node)

        mock_repo_repo = MagicMock()
        mock_repo_repo.get = AsyncMock(return_value=mock_repo)

        result = await git_status_handler(
            node_id="test-node-1",
            repo_id="test-repo-1",
            node_client=mock_node_client,
            node_repo=mock_node_repo,
            repo_repo=mock_repo_repo,
        )

        assert result["success"] is True
        assert "branch" in result
        assert "is_clean" in result
        assert "is_dirty" in result
        assert "staged" in result
        assert "modified" in result
        assert "untracked" in result
        # Check that both boolean fields are present and consistent
        assert result["is_clean"] != result["is_dirty"]

    @pytest.mark.asyncio
    async def test_git_status_node_not_found(self, mock_node_client):
        """Test git_status when node doesn't exist."""
        mock_node_repo = MagicMock()
        mock_node_repo.get = AsyncMock(return_value=None)

        result = await git_status_handler(
            node_id="nonexistent-node",
            repo_id="test-repo-1",
            node_client=mock_node_client,
            node_repo=mock_node_repo,
            repo_repo=MagicMock(),
        )

        assert result["success"] is False
        assert "not found" in result["error"].lower()


# ============================================================================
# Write Tool Tests
# ============================================================================


class TestWriteTools:
    """Tests for write_markdown tool."""

    @pytest.mark.asyncio
    async def test_write_markdown_validates_extension(
        self,
        mock_node_client,
        mock_node,
        mock_repo,
    ):
        """Test that write_markdown validates file extensions."""
        mock_node_repo = MagicMock()
        mock_node_repo.get = AsyncMock(return_value=mock_node)

        mock_write_target_repo = MagicMock()
        mock_write_target_policy = MagicMock()
        mock_write_target_policy.list_write_targets_for_repo = AsyncMock(
            return_value=[mock_write_target]
        )

        # Try to write a file with disallowed extension
        result = await write_markdown_handler(
            node_id="test-node-1",
            repo_id="test-repo-1",
            path="script.py",  # .py not in allowed extensions
            content="# Python script",
            node_client=mock_node_client,
            node_repo=mock_node_repo,
            write_target_repo=mock_write_target_repo,
            write_target_policy=mock_write_target_policy,
        )

        assert result["success"] is False
        assert "extension" in result["error"].lower() or "allowed" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_write_markdown_requires_write_target(
        self,
        mock_node_client,
        mock_node,
    ):
        """Test that write_markdown requires configured write targets."""
        mock_node_repo = MagicMock()
        mock_node_repo.get = AsyncMock(return_value=mock_node)

        mock_write_target_repo = MagicMock()
        mock_write_target_policy = MagicMock()
        mock_write_target_policy.list_write_targets_for_repo = AsyncMock(
            return_value=[]  # No write targets
        )

        result = await write_markdown_handler(
            node_id="test-node-1",
            repo_id="test-repo-1",
            path="test.md",
            content="# Test content",
            node_client=mock_node_client,
            node_repo=mock_node_repo,
            write_target_repo=mock_write_target_repo,
            write_target_policy=mock_write_target_policy,
        )

        assert result["success"] is False
        assert "no write targets" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_write_markdown_success(
        self,
        mock_node_client,
        mock_node,
        mock_write_target,
    ):
        """Test successful write_markdown call."""
        mock_node_repo = MagicMock()
        mock_node_repo.get = AsyncMock(return_value=mock_node)

        mock_repo = MagicMock()
        mock_repo.repo_id = "test-repo-1"
        mock_repo.path = "/home/test/repo"

        mock_repo_repo = MagicMock()
        mock_repo_repo.get = AsyncMock(return_value=mock_repo)

        mock_write_target_repo = MagicMock()
        mock_write_target_policy = MagicMock()
        mock_write_target_policy.list_write_targets_for_repo = AsyncMock(
            return_value=[mock_write_target]
        )
        mock_write_target_policy.validate_write_access = AsyncMock()

        result = await write_markdown_handler(
            node_id="test-node-1",
            repo_id="test-repo-1",
            path="test.md",
            content="# Test content",
            node_client=mock_node_client,
            node_repo=mock_node_repo,
            write_target_repo=mock_write_target_repo,
            write_target_policy=mock_write_target_policy,
        )

        assert result["success"] is True
        assert "sha256_hash" in result
        assert result["verified"] is True

    @pytest.mark.asyncio
    async def test_write_markdown_path_traversal_rejected(
        self,
        mock_node_client,
        mock_node,
        mock_write_target,
    ):
        """Test that path traversal is rejected in writes."""
        mock_node_repo = MagicMock()
        mock_node_repo.get = AsyncMock(return_value=mock_node)

        mock_repo = MagicMock()
        mock_repo.repo_id = "test-repo-1"
        mock_repo.path = "/home/test/repo"

        mock_repo_repo = MagicMock()
        mock_repo_repo.get = AsyncMock(return_value=mock_repo)

        mock_write_target_repo = MagicMock()
        mock_write_target_policy = MagicMock()
        mock_write_target_policy.list_write_targets_for_repo = AsyncMock(
            return_value=[mock_write_target]
        )

        result = await write_markdown_handler(
            node_id="test-node-1",
            repo_id="test-repo-1",
            path="../secret.txt",
            content="# Secret",
            node_client=mock_node_client,
            node_repo=mock_node_repo,
            write_target_repo=mock_write_target_repo,
            write_target_policy=mock_write_target_policy,
        )

        assert result["success"] is False
        assert (
            "validation failed" in result["error"].lower() or "traversal" in result["error"].lower()
        )


# ============================================================================
# LLM Tool Tests
# ============================================================================


class TestLLMTools:
    """Tests for chat_llm tool."""

    @pytest.mark.asyncio
    async def test_chat_llm_requires_service_alias(self):
        """Test that chat_llm requires service identification."""
        result = await chat_llm_handler(
            prompt="Hello",
            llm_service_policy=MagicMock(),
            llm_client=MagicMock(),
        )

        # Should fail because no service or task_class provided
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_chat_llm_requires_prompt(self):
        """Test that chat_llm requires a prompt."""
        result = await chat_llm_handler(
            prompt="",
            service_id="test-service",
            llm_service_policy=MagicMock(),
            llm_client=MagicMock(),
        )

        assert result["success"] is False
        assert "prompt" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_chat_llm_returns_structured_response(
        self,
        mock_llm_service,
        mock_llm_client,
    ):
        """Test that chat_llm returns properly structured response."""
        mock_policy = MagicMock()
        mock_policy.validate_service_access = AsyncMock(return_value=mock_llm_service)

        result = await chat_llm_handler(
            service_id="test-service-1",
            prompt="Hello, how are you?",
            llm_service_policy=mock_policy,
            llm_client=mock_llm_client,
        )

        assert result["success"] is True
        assert "response" in result
        assert "service_id" in result
        assert "latency_ms" in result

    @pytest.mark.asyncio
    async def test_chat_llm_invalid_service_rejected(self):
        """Test that invalid service is rejected."""
        mock_policy = MagicMock()
        mock_policy.validate_service_access = AsyncMock(side_effect=ValueError("Service not found"))

        result = await chat_llm_handler(
            service_id="invalid-service",
            prompt="Hello",
            llm_service_policy=mock_policy,
            llm_client=MagicMock(),
        )

        assert result["success"] is False
        assert "validation failed" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_chat_llm_with_task_routing(self, mock_llm_client):
        """Test chat_llm with task_class for auto-routing."""
        mock_policy = MagicMock()
        mock_routing_policy = MagicMock()
        mock_routing_policy.get_fallback_chain = AsyncMock(return_value=[])

        result = await chat_llm_handler(
            prompt="Hello",
            task_routing_policy=mock_routing_policy,
            llm_service_policy=mock_policy,
            llm_client=mock_llm_client,
        )

        # Should fail gracefully when no services available
        assert result["success"] is False


# ============================================================================
# Failure Mode Tests
# ============================================================================


class TestFailureModes:
    """Tests for failure mode handling across tools."""

    @pytest.mark.asyncio
    async def test_unknown_node_rejected(self, mock_node_client):
        """Test that unknown nodes are rejected."""
        mock_node_repo = MagicMock()
        mock_node_repo.get = AsyncMock(return_value=None)

        result = await inspect_repo_tree_handler(
            node_id="unknown-node-123",
            repo_id="test-repo-1",
            node_client=mock_node_client,
            node_repo=mock_node_repo,
            repo_repo=MagicMock(),
        )

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_unknown_repo_rejected(
        self,
        mock_node_client,
        mock_node,
    ):
        """Test that unknown repos are rejected."""
        mock_node_repo = MagicMock()
        mock_node_repo.get = AsyncMock(return_value=mock_node)

        mock_repo_repo = MagicMock()
        mock_repo_repo.get = AsyncMock(return_value=None)

        result = await inspect_repo_tree_handler(
            node_id="test-node-1",
            repo_id="unknown-repo-123",
            node_client=mock_node_client,
            node_repo=mock_node_repo,
            repo_repo=mock_repo_repo,
        )

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_invalid_path_rejected(
        self,
        mock_node_client,
        mock_node,
        mock_repo,
    ):
        """Test that invalid paths are rejected."""
        mock_node_repo = MagicMock()
        mock_node_repo.get = AsyncMock(return_value=mock_node)

        mock_repo_repo = MagicMock()
        mock_repo_repo.get = AsyncMock(return_value=mock_repo)

        # Try various path traversal attempts
        invalid_paths = [
            "../../../etc/passwd",
            "/absolute/path",
            "foo/../../bar",
            "foo/./bar",
        ]

        for invalid_path in invalid_paths:
            result = await read_repo_file_handler(
                node_id="test-node-1",
                repo_id="test-repo-1",
                file_path=invalid_path,
                node_client=mock_node_client,
                node_repo=mock_node_repo,
                repo_repo=mock_repo_repo,
            )
            # Path should either be rejected or validated
            assert (
                result.get("success") is False
                or "validation failed" in result.get("error", "").lower()
            )

    @pytest.mark.asyncio
    async def test_missing_required_params_rejected(self):
        """Test that missing required parameters are rejected."""
        # Test various handlers with missing parameters

        # inspect_repo_tree - missing node_id and repo_id
        result = await inspect_repo_tree_handler(
            node_id="",
            repo_id="",
        )
        assert result["success"] is False

        # search_repo - missing pattern
        result = await search_repo_handler(
            node_id="test-node",
            repo_id="test-repo",
            pattern="",
        )
        assert result["success"] is False

        # write_markdown - missing content
        mock_node_repo = MagicMock()
        mock_node_repo.get = AsyncMock(return_value=MagicMock())

        result = await write_markdown_handler(
            node_id="test-node",
            repo_id="test-repo",
            path="test.md",
            content="",
            node_client=MagicMock(),
            node_repo=mock_node_repo,
            write_target_repo=MagicMock(),
            write_target_policy=MagicMock(),
        )
        assert result["success"] is False

        # chat_llm - missing prompt
        result = await chat_llm_handler(
            service_id="test-service",
            prompt="",
            llm_service_policy=MagicMock(),
            llm_client=MagicMock(),
        )
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_node_client_not_available(self):
        """Test handlers properly report when node client is unavailable."""
        mock_node_repo = MagicMock()
        mock_node_repo.get = AsyncMock(return_value=MagicMock())

        mock_repo_repo = MagicMock()
        mock_repo_repo.get = AsyncMock(return_value=MagicMock())

        result = await inspect_repo_tree_handler(
            node_id="test-node",
            repo_id="test-repo",
            node_client=None,
            node_repo=mock_node_repo,
            repo_repo=mock_repo_repo,
        )

        assert result["success"] is False
        assert "not available" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_repository_not_available(self):
        """Test handlers properly report when repository is unavailable."""
        result = await list_repos_handler(repo_repo=None)
        assert "error" in result

        result = await inspect_repo_tree_handler(
            node_id="test-node",
            repo_id="test-repo",
            node_client=MagicMock(),
            node_repo=MagicMock(),
            repo_repo=None,
        )
        assert result["success"] is False

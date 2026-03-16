"""Hub-to-node HTTP client for communicating with node agents."""

from datetime import datetime, timezone
from typing import Any

import httpx

from src.hub.services.auth import NodeAuthHandler
from src.shared.logging import get_logger
from src.shared.models import NodeInfo
from src.shared.schemas import NodeHealthResponse

logger = get_logger(__name__)


class HubNodeClient:
    """HTTP client for hub-to-node communication over Tailscale.

    This client provides a structured interface for making authenticated
    HTTP requests to node agents, with configurable timeouts and
    connection pooling.
    """

    def __init__(
        self,
        http_client: httpx.AsyncClient,
        auth_handler: NodeAuthHandler,
        default_timeout: float = 30.0,
        connect_timeout: float = 5.0,
    ):
        """Initialize the hub node client.

        Args:
            http_client: The underlying async HTTP client.
            auth_handler: Authentication handler for node requests.
            default_timeout: Default request timeout in seconds.
            connect_timeout: Connection timeout in seconds.
        """
        self._client = http_client
        self._auth = auth_handler
        self._default_timeout = default_timeout
        self._connect_timeout = connect_timeout

    async def request(
        self,
        node: NodeInfo,
        method: str,
        path: str,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make an authenticated request to a node.

        Args:
            node: The target node information.
            method: HTTP method (GET, POST, etc.).
            path: URL path for the request.
            timeout: Optional timeout override in seconds.
            **kwargs: Additional arguments passed to httpx request.

        Returns:
            The HTTP response from the node.
        """
        url = f"http://{node.hostname}{path}"
        headers = self._auth.get_headers()

        # Merge any additional headers
        extra_headers = kwargs.pop("headers", {})
        headers.update(extra_headers)

        timeout_value = timeout or self._default_timeout

        logger.debug(
            "node_request",
            node_id=node.node_id,
            method=method,
            url=url,
            timeout=timeout_value,
        )

        response = await self._client.request(
            method=method,
            url=url,
            headers=headers,
            timeout=timeout_value,
            **kwargs,
        )

        # Validate authentication response
        try:
            self._auth.validate_response(response)
        except Exception:
            logger.warning(
                "node_response_auth_warning",
                node_id=node.node_id,
                status_code=response.status_code,
            )
            raise

        return response

    async def get(
        self,
        node: NodeInfo,
        path: str,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make a GET request to a node.

        Args:
            node: The target node information.
            path: URL path for the request.
            timeout: Optional timeout override.
            **kwargs: Additional arguments for the request.

        Returns:
            The HTTP response from the node.
        """
        return await self.request(node, "GET", path, timeout=timeout, **kwargs)

    async def post(
        self,
        node: NodeInfo,
        path: str,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make a POST request to a node.

        Args:
            node: The target node information.
            path: URL path for the request.
            timeout: Optional timeout override.
            **kwargs: Additional arguments for the request.

        Returns:
            The HTTP response from the node.
        """
        return await self.request(node, "POST", path, timeout=timeout, **kwargs)

    async def health_check(self, node: NodeInfo) -> NodeHealthResponse:
        """Perform a health check on a node.

        Args:
            node: The node to check.

        Returns:
            NodeHealthResponse with health status from the node.
        """
        response = await self.get(node, "/health", timeout=10.0)

        if response.status_code == 200:
            try:
                data = response.json()
                return NodeHealthResponse(
                    node_id=node.node_id,
                    status=data.get("status", "healthy"),
                    last_check=data.get("timestamp"),
                    latency_ms=data.get("latency_ms"),
                    error=data.get("error"),
                )
            except Exception as e:
                logger.warning(
                    "node_health_json_parse_error",
                    node_id=node.node_id,
                    error=str(e),
                )
                return NodeHealthResponse(
                    node_id=node.node_id,
                    status="unhealthy",
                    error=f"JSON parse error: {str(e)}",
                )

        # Return error response
        return NodeHealthResponse(
            node_id=node.node_id,
            status="unhealthy",
            error=f"HTTP {response.status_code}",
        )

    async def read_file(
        self,
        node: NodeInfo,
        path: str,
    ) -> dict[str, Any]:
        """Read a file from a node.

        Args:
            node: The target node.
            path: Path to the file to read.

        Returns:
            Dictionary with file content or error.
        """
        response = await self.get(node, f"/files/read?path={path}", timeout=30.0)

        if response.status_code == 200:
            return response.json()

        return {
            "success": False,
            "error": f"Failed to read file: HTTP {response.status_code}",
        }

    async def write_file(
        self,
        node: NodeInfo,
        path: str,
        content: str,
    ) -> dict[str, Any]:
        """Write a file to a node.

        Args:
            node: The target node.
            path: Path to the file to write.
            content: File content to write.

        Returns:
            Dictionary with success status or error.
        """
        response = await self.post(
            node,
            "/files/write",
            json={"path": path, "content": content},
            timeout=30.0,
        )

        if response.status_code == 200:
            return response.json()

        return {
            "success": False,
            "error": f"Failed to write file: HTTP {response.status_code}",
        }

    async def search(
        self,
        node: NodeInfo,
        query: str,
        path: str | None = None,
    ) -> dict[str, Any]:
        """Search within a node's repos.

        Args:
            node: The target node.
            query: Search query string.
            path: Optional path to limit search.

        Returns:
            Dictionary with search results or error.
        """
        params = {"query": query}
        if path:
            params["path"] = path

        response = await self.get(node, "/search", params=params, timeout=60.0)

        if response.status_code == 200:
            return response.json()

        return {
            "success": False,
            "error": f"Search failed: HTTP {response.status_code}",
        }

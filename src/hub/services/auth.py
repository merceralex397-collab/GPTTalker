"""Authentication handler for hub-to-node communication."""

import httpx

from src.shared.logging import get_logger

logger = get_logger(__name__)


class NodeAuthError(Exception):
    """Exception raised for node authentication failures."""

    pass


class NodeAuthHandler:
    """Handles authentication for hub-to-node requests.

    This handler manages API key-based authentication for HTTP requests
    to node agents over Tailscale.
    """

    GPTTALKER_VERSION = "1.0.0"

    def __init__(self, api_key: str | None = None):
        """Initialize the authentication handler.

        Args:
            api_key: Optional API key for node authentication.
        """
        self._api_key = api_key

    def get_headers(self) -> dict[str, str]:
        """Get authentication headers for node requests.

        Returns:
            Dictionary of headers including version and auth token.
        """
        headers = {
            "X-GPTTalker-Version": self.GPTTALKER_VERSION,
        }
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
            logger.debug("auth_headers_with_bearer", api_key_present=True)
        else:
            logger.debug("auth_headers_no_bearer", api_key_present=False)
        return headers

    def validate_response(self, response: httpx.Response) -> None:
        """Validate response authentication status.

        Args:
            response: The HTTP response to validate.

        Raises:
            NodeAuthError: If authentication or authorization failed.
        """
        if response.status_code == 401:
            logger.warning(
                "node_auth_failed",
                status_code=response.status_code,
                url=str(response.url),
            )
            raise NodeAuthError("Node authentication failed: invalid or missing credentials")

        if response.status_code == 403:
            logger.warning(
                "node_auth_forbidden",
                status_code=response.status_code,
                url=str(response.url),
            )
            raise NodeAuthError("Node authorization failed: insufficient permissions")

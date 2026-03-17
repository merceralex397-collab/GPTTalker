"""HTTP client for embedding service communication."""

import time
from typing import Any

import httpx

from src.shared.logging import get_logger
from src.shared.models import LLMServiceInfo

logger = get_logger(__name__)


class EmbeddingServiceClient:
    """HTTP client for embedding services.

    This client handles embedding generation requests to services like
    OpenAI-compatible embedding endpoints. It supports single and batch
    embedding requests with appropriate timeout handling.
    """

    def __init__(
        self,
        http_client: httpx.AsyncClient,
        default_timeout: float = 30.0,
    ):
        """Initialize the embedding service client.

        Args:
            http_client: The underlying async HTTP client.
            default_timeout: Default request timeout in seconds (30s for embeddings).
        """
        self._client = http_client
        self._default_timeout = default_timeout

    async def embed(
        self,
        service: LLMServiceInfo,
        text: str,
        encoding_format: str = "float",
    ) -> dict[str, Any]:
        """Generate embeddings for a single text input.

        Args:
            service: Embedding service configuration.
            text: Text to generate embeddings for.
            encoding_format: Encoding format (float, base64, or int8).

        Returns:
            Dictionary with embeddings and metadata.
        """
        return await self.embed_batch(service, texts=[text], encoding_format=encoding_format)

    async def embed_batch(
        self,
        service: LLMServiceInfo,
        texts: list[str],
        encoding_format: str = "float",
    ) -> dict[str, Any]:
        """Generate embeddings for multiple text inputs.

        Args:
            service: Embedding service configuration.
            texts: List of texts to generate embeddings for.
            encoding_format: Encoding format (float, base64, or int8).

        Returns:
            Dictionary with embeddings list, model, and metadata.
        """
        start_time = int(time.time() * 1000)

        # Validate inputs
        if not texts:
            return {
                "success": False,
                "error": "No texts provided",
                "latency_ms": 0,
            }

        if not service.endpoint:
            return {
                "success": False,
                "error": "Service endpoint not configured",
                "latency_ms": 0,
            }

        # Build request payload (OpenAI-compatible format)
        payload = self._build_payload(texts, encoding_format)

        # Build headers
        headers = {"Content-Type": "application/json"}
        if service.api_key:
            headers["Authorization"] = f"Bearer {service.api_key}"

        # Make the request with timeout handling
        try:
            response = await self._client.post(
                service.endpoint,
                json=payload,
                timeout=self._default_timeout,
                headers=headers,
            )
            response.raise_for_status()
            result = response.json()

        except httpx.TimeoutException:
            latency_ms = int(time.time() * 1000) - start_time
            logger.error(
                "embedding_request_timeout",
                service_id=service.service_id,
                timeout=self._default_timeout,
                text_count=len(texts),
                latency_ms=latency_ms,
            )
            return {
                "success": False,
                "error": f"Request timeout after {self._default_timeout}s",
                "latency_ms": latency_ms,
            }

        except httpx.HTTPStatusError as e:
            latency_ms = int(time.time() * 1000) - start_time
            logger.error(
                "embedding_request_failed",
                service_id=service.service_id,
                status_code=e.response.status_code,
                text_count=len(texts),
                latency_ms=latency_ms,
            )
            return {
                "success": False,
                "error": f"HTTP error: {e.response.status_code}",
                "latency_ms": latency_ms,
            }

        except Exception as e:
            latency_ms = int(time.time() * 1000) - start_time
            logger.error(
                "embedding_request_error",
                service_id=service.service_id,
                error=str(e),
                text_count=len(texts),
                latency_ms=latency_ms,
            )
            return {
                "success": False,
                "error": f"Request failed: {e}",
                "latency_ms": latency_ms,
            }

        # Parse response
        parsed = self._parse_response(result)
        latency_ms = int(time.time() * 1000) - start_time

        logger.info(
            "embedding_request_success",
            service_id=service.service_id,
            text_count=len(texts),
            embedding_dim=len(parsed.get("embeddings", [[]])[0]) if parsed.get("embeddings") else 0,
            latency_ms=latency_ms,
        )

        return {
            "success": True,
            **parsed,
            "latency_ms": latency_ms,
        }

    def _build_payload(
        self,
        texts: list[str],
        encoding_format: str,
    ) -> dict[str, Any]:
        """Build embedding request payload.

        Args:
            texts: List of texts to embed.
            encoding_format: Encoding format for embeddings.

        Returns:
            OpenAI-compatible embedding request payload.
        """
        return {
            "input": texts,
            "model": "text-embedding-ada-002",  # Default, can be overridden by service
            "encoding_format": encoding_format,
        }

    def _parse_response(self, response: dict[str, Any]) -> dict[str, Any]:
        """Parse embedding service response into standardized format.

        Args:
            response: Raw embedding service response.

        Returns:
            Parsed response with standardized fields.
        """
        # OpenAI-compatible response format
        if "data" in response and response["data"]:
            embeddings = [item.get("embedding", []) for item in response["data"]]
            model = response.get("model")
            tokens_used = response.get("usage", {}).get("total_tokens")

            return {
                "embeddings": embeddings,
                "model": model,
                "tokens_used": tokens_used,
            }

        # Fallback: handle other common formats
        if "embedding" in response:
            return {
                "embeddings": [response["embedding"]],
                "model": response.get("model"),
                "tokens_used": response.get("tokens_used"),
            }

        if "embeddings" in response:
            return {
                "embeddings": response["embeddings"],
                "model": response.get("model"),
                "tokens_used": response.get("tokens_used"),
            }

        # Return empty on unrecognized format
        logger.warning(
            "embedding_unrecognized_response_format", response_keys=list(response.keys())
        )
        return {
            "embeddings": [],
            "model": None,
            "tokens_used": None,
        }
